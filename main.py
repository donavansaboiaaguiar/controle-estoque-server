from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

app = FastAPI(title="Controle Estoque API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Models ─────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    nome: str
    senha: str

class DadosRequest(BaseModel):
    chave: str
    valor: Any
    usuario: str

class DadosResponse(BaseModel):
    chave: str
    valor: Any
    atualizado_em: Optional[str]
    atualizado_por: Optional[str]


# ── Login ───────────────────────────────────────────────────────
@app.post("/login")
def login(req: LoginRequest):
    db = get_db()
    res = db.table("usuarios").select("*").eq("nome", req.nome).eq("senha", req.senha).eq("ativo", True).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="Usuario ou senha incorretos")
    return {"ok": True, "nome": res.data[0]["nome"]}


# ── Dados ───────────────────────────────────────────────────────
@app.get("/dados/{chave}")
def get_dados(chave: str):
    db = get_db()
    res = db.table("dados").select("*").eq("chave", chave).execute()
    if not res.data:
        return {"chave": chave, "valor": None}
    return res.data[0]


@app.post("/dados")
def set_dados(req: DadosRequest):
    db = get_db()
    from datetime import datetime
    payload = {
        "chave":          req.chave,
        "valor":          req.valor,
        "atualizado_em":  datetime.utcnow().isoformat(),
        "atualizado_por": req.usuario,
    }
    db.table("dados").upsert(payload).execute()
    # Log
    db.table("alteracoes").insert({
        "usuario":   req.usuario,
        "chave":     req.chave,
        "descricao": f"Atualizou {req.chave}",
    }).execute()
    return {"ok": True}


@app.get("/dados")
def list_dados():
    db = get_db()
    res = db.table("dados").select("chave, atualizado_em, atualizado_por").execute()
    return res.data


# ── Usuarios ────────────────────────────────────────────────────
@app.get("/usuarios")
def list_usuarios():
    db = get_db()
    res = db.table("usuarios").select("id, nome, ativo").execute()
    return res.data


@app.post("/usuarios")
def add_usuario(nome: str, senha: str):
    db = get_db()
    db.table("usuarios").insert({"nome": nome, "senha": senha}).execute()
    return {"ok": True}


@app.get("/ping")
def ping():
    return {"status": "ok"}
