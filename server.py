import os
import yaml
import secrets
import random
from openai import AsyncOpenAI
from dotenv import load_dotenv
from datetime import datetime,timezone
from pydantic import BaseModel, Field
from typing import Optional, Union, List
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from clinents import call_google, call_groq, call_huggingface, call_openrouter, pick_model, call_opencode_zen, call_cerebras, call_nvidia
from database import create_api_key, verify_key, add_token_usage, get_usage_by_key, get_user_keys_info, revoke_api_key, count_user_keys, save_provider_key, get_provider_key, list_provider_keys, delete_provider_key, decrypt_value

load_dotenv()
def get_real_ip(request: Request):
    forwarded=request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)

limiter=Limiter(key_func=get_real_ip)
app=FastAPI()
app.state.limiter=limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

starttime=datetime.now(timezone.utc)

with open('models.yaml', 'r', encoding='UTF-8') as f:
    config=yaml.safe_load(f)['models']

class Userrequest(BaseModel):
    messages: Union[List[dict], str]=Field(...)
    model: str

class Modelinfo(BaseModel):
    name: str
    slug: str
    provider: str
    tier: str
    kind: str

class KeyInfo(BaseModel):
    api_key: str
    created_at: Optional[str] = None
    used_tokens: int

class Revokekey(BaseModel):
    email: str
    apikey: str

class ProviderKeyRequest(BaseModel):
    provider: str
    provider_key: str = Field(..., min_length=5, max_length=500)

@app.get('/')
async def root():
    try:
        return {'status': 'ok', "message": "AI Router API is running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/generate-key')
@limiter.limit('10/hour')
async def generate_key(request: Request, email: str | None = None):
    if email:
        key_count = count_user_keys(email)
        if key_count >= 2:
            return {'error': 'limit_reached', 'message': 'Maximum of 2 API keys reached.'}
    newkey=secrets.token_urlsafe(32)
    create_api_key(newkey, email)
    return {'API key': newkey}

async def verify(
    apikey: Optional[str]=Header(None),
    authorization: Optional[str]=Header(None)
) -> str:
    token=apikey
    if not token and authorization:
        if authorization.startswith("Bearer "):
            token=authorization.split(" ", 1)[1]
        else:
            token=authorization

    if not token or not verify_key(token):
        raise HTTPException(status_code=401, detail='Invalid or inactive API key')
    return token

async def modelverify(model: str):
    available=[m['slug'] for m in config]
    for m in config:
        if model == m['name'] or model == m['slug']:
            modelinfo={'realname': m['name'], 'slug': m['slug'], 'provider': m['provider']}
            return modelinfo
    raise ValueError(f"Unknown model '{model}'. Available slugs: {available}")

PROVIDER_BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1","openrouter": "https://openrouter.ai/api/v1","google": "https://generativelanguage.googleapis.com/v1beta/openai/","huggingface": "https://router.huggingface.co/v1","opencode_zen": "https://opencode.ai/zen/v1","cerebras": "https://api.cerebras.ai/v1","nvidia": "https://integrate.api.nvidia.com/v1",}

CALL_FUNCTIONS = {
    "openrouter": call_openrouter,
    "groq": call_groq,
    "google": call_google,
    "huggingface": call_huggingface,
    "opencode_zen": call_opencode_zen,
    "cerebras": call_cerebras,
    "nvidia": call_nvidia}

async def call_with_optional_user_key(provider: str, model: str, messages: list[dict], apikey: str, **kwargs) -> dict:
    user_key = get_provider_key(apikey, provider) 

    if user_key:
        temp_client = AsyncOpenAI(base_url=PROVIDER_BASE_URLS[provider], api_key=user_key)
        response = await temp_client.chat.completions.create(model=model, messages=messages, **kwargs)
        return response.model_dump()
    else:
        return await CALL_FUNCTIONS[provider](model, messages, **kwargs)
 
@app.post('/v1/chat/completions')
@app.post('/chat/completions')
@limiter.limit('20/minute')
async def chat(request: Request, payload: Userrequest, apikey: str = Depends(verify)):
    if isinstance(payload.messages, str):
        messages = [{'role': 'user', 'content': payload.messages}]
    else:
        messages=payload.messages

    if payload.model == 'openrouter/auto':
        openroutermodels = [m['name'] for m in config if m['provider'] == 'openrouter']
        result = await call_openrouter(
            'openrouter/auto', messages,
            extra_body={"models": random.sample(openroutermodels, min(3, len(openroutermodels)))},
            max_tokens=2000)

    elif payload.model == 'openllm/auto':
        chosenslug= await pick_model(messages)
        modelname = await modelverify(chosenslug)
        result = await call_with_optional_user_key(modelname['provider'], modelname['realname'], messages, apikey, max_tokens=2000)

    else:
        try:
            modelname = await modelverify(payload.model)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        result=await call_with_optional_user_key(modelname['provider'], modelname['realname'], messages, apikey, max_tokens=2000)

    tokens_used = 0
    if isinstance(result, dict):
        usage = result.get("usage") or {}
        tokens_used = usage.get("total_tokens", 0)

    if tokens_used > 0:
        add_token_usage(apikey, tokens_used)

    return result

@app.get('/models')
@limiter.limit('20/minute')
async def listmodels(request: Request):
    try:
        names=[m['name'] for m in config]
        return names
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/model/{name}')
@limiter.limit('20/minute')
async def getmodelinfo(request: Request, slug: str):
    try:
        for m in config:
            if slug == m['slug'] or slug == m['name']:
                return Modelinfo(**m)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/usage')
@limiter.limit('20/minute')
async def getusage(request: Request, apikey:str=Header(...), _=Depends(verify)):
    try:
        usedtokens=get_usage_by_key(apikey)
        return {'date': datetime.now().strftime('%d/%m/%y - %H:%M:%S'),
                'apikey': f'{apikey[:6]}...',
                'usage': f'{usedtokens} Tokens'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/serverinfo')
@limiter.limit('20/minute')
async def serverinfo(request: Request):
    now=datetime.now(timezone.utc)
    uptime=int((now-starttime).total_seconds())
    return {'status': 'ok',
            'service': 'openllm-api',
            'version': os.getenv('version'),
            "environment": os.getenv("ENVIRONMENT"),
            'uptime_seconds': uptime,
            'models': len(config),
            'database_ready': bool(os.getenv('supabase_url')),
            'providers': len({item['provider'] for item in config if item.get('provider')})}

@app.get('/keys', response_model=list[KeyInfo])
@limiter.limit('10/minute')
async def getkeys(request: Request, email: Optional[str]=None):
    try:
        keydata=get_user_keys_info(email)
        formatted_keys = []
        for item in keydata:
            raw_key = item["api_key"]
            masked_key = f"{raw_key[:6]}...{raw_key[-4:]}" if len(raw_key) > 10 else raw_key
            
            formatted_keys.append(
                KeyInfo(
                    api_key=masked_key,
                    created_at=str(item["created_at"]) if item["created_at"] else "N/A",
                    used_tokens=item["used_tokens"]))
            
        return formatted_keys
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete('/revokekey')
@limiter.limit('10/hour')
async def revokekey(request: Request, body: Revokekey):
    succes=revoke_api_key(email=body.email, key_to_revoke=body.apikey)
    if not succes:
        raise HTTPException(status_code=404, detail='The API key does not exist or has expired.')

    return {'status': 'ok',
            'massage': 'The API key has been revoked.'}

SUPPORTEDPROVIDERS = ["groq", "openrouter", "google", "huggingface", "opencode_zen", "cerebras", "nvidia"]

@app.post('/keys/provider')
@limiter.limit('20/minute')
async def set_provider_key(request: Request, payload: ProviderKeyRequest, apikey: str = Header(...), _=Depends(verify)):
    if payload.provider not in SUPPORTEDPROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider '{payload.provider}'. Supported: {SUPPORTEDPROVIDERS}")

    save_provider_key(apikey, payload.provider, payload.provider_key)
    return {"status": "saved", "provider": payload.provider}

@app.get('/keys/provider')
async def get_my_provider_keys(apikey: str = Header(...), _=Depends(verify)):
    keys = list_provider_keys(apikey)
    result = []
    for k in keys:
        try:
            decrypted = decrypt_value(k['provider_key_encrypted'])
            preview = f"{decrypted[:6]}...{decrypted[-4:]}" if len(decrypted) > 10 else "***"
        except Exception:
            preview = "***"
        result.append({"provider": k['provider'], "key_preview": preview})
    return result

@app.delete('/keys/provider/{provider}')
async def remove_provider_key(provider: str, apikey: str = Header(...), _=Depends(verify)):
    if provider not in SUPPORTEDPROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider '{provider}'")
    delete_provider_key(apikey, provider)
    return {"status": "deleted", "provider": provider}



        

    

    

    
