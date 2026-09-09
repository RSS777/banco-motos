# banco-motos

Pipeline pessoal de garimpo de vídeos curtos sobre moto elétrica (YouTube + TikTok), análise e geração de roteiro via Gemini, armazenamento no Supabase. Ver a spec completa na issue [#1](https://github.com/RSS777/banco-motos/issues/1).

## Setup local

```
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt
.venv/Scripts/scrapling install   # baixa os binários do Camoufox/Playwright usados pelo coletor TikTok
```

Copie `.env.example` para `.env` e preencha as chaves (não é lido automaticamente — exporte as variáveis no seu shell antes de rodar testes de integração).

## Testes

```
.venv/Scripts/pytest
```

Os testes de integração (que batem em APIs reais) são pulados automaticamente sem as credenciais correspondentes no ambiente. O teste de integração do TikTok exige, além disso, `RUN_TIKTOK_INTEGRATION=1` (é lento e sujeito ao rate limiting do próprio TikTok).
