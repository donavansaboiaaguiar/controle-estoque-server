from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
import os, httpx

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

app = FastAPI(title="Controle Estoque API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

class LoginRequest(BaseModel):
    nome: str
    senha: str

class DadosRequest(BaseModel):
    chave: str
    valor: Any
    usuario: str

@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.post("/login")
def login(req: LoginRequest):
    r = httpx.get(f"{SUPABASE_URL}/rest/v1/usuarios",
                  headers=headers(),
                  params={"nome": f"eq.{req.nome}",
                          "senha": f"eq.{req.senha}",
                          "ativo": "eq.true"})
    data = r.json()
    if not data:
        raise HTTPException(status_code=401, detail="Usuario ou senha incorretos")
    return {"ok": True, "nome": data[0]["nome"]}

@app.get("/dados/{chave}")
def get_dados(chave: str):
    r = httpx.get(f"{SUPABASE_URL}/rest/v1/dados",
                  headers=headers(),
                  params={"chave": f"eq.{chave}"})
    data = r.json()
    if not data:
        return {"chave": chave, "valor": None}
    return data[0]

@app.post("/dados")
def set_dados(req: DadosRequest):
    payload = {
        "chave": req.chave,
        "valor": req.valor,
        "atualizado_em": datetime.utcnow().isoformat(),
        "atualizado_por": req.usuario
    }
    httpx.post(f"{SUPABASE_URL}/rest/v1/dados",
               headers={**headers(), "Prefer": "resolution=merge-duplicates"},
               json=payload)
    httpx.post(f"{SUPABASE_URL}/rest/v1/alteracoes",
               headers=headers(),
               json={"usuario": req.usuario, "chave": req.chave,
                     "descricao": f"Atualizou {req.chave}"})
    return {"ok": True}

@app.get("/dados")
def list_dados():
    r = httpx.get(f"{SUPABASE_URL}/rest/v1/dados",
                  headers=headers(),
                  params={"select": "chave,atualizado_em,atualizado_por"})
    return r.json()

@app.get("/usuarios")
def list_usuarios():
    r = httpx.get(f"{SUPABASE_URL}/rest/v1/usuarios",
                  headers=headers(),
                  params={"select": "id,nome,ativo"})
    return r.json()

@app.post("/usuarios")
def add_usuario(nome: str, senha: str):
    httpx.post(f"{SUPABASE_URL}/rest/v1/usuarios",
               headers=headers(),
               json={"nome": nome, "senha": senha})
    return {"ok": True}
