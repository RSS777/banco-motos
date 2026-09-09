# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

HTML/CSS/JS estático, sem framework, consumindo o Supabase diretamente via client JS (REST/SDK) do navegador, sem backend intermediário. Hospedado no GitHub Pages.

## Users

Usuário único, dono do projeto: um criador de conteúdo sobre moto elétrica que precisa de um fluxo diário de temas/ganchos de roteiro para gravar seu próprio conteúdo. Não há outros usuários ou público externo — é uma ferramenta pessoal de uso interno.

## Product Purpose

Um "banco de conteúdo" pessoal que garimpa automaticamente vídeos curtos sobre moto elétrica (YouTube via API oficial, TikTok via scraping), usa a Gemini API para analisar cada vídeo e gerar um roteiro original em pt-BR inspirado no formato/gancho encontrado, e entrega isso revisável num PWA — para que o usuário nunca fique sem ideia de conteúdo pra gravar. Sucesso é: todo dia, sem esforço manual, existe uma lista nova de roteiros prontos pra revisão.

## Positioning

Não é um produto vendido nem um agregador público — é um pipeline pessoal e automatizado que combina descoberta multi-plataforma, análise por IA e geração de roteiro numa única passada diária, sem exigir curadoria manual do usuário nem reaproveitar diretamente o conteúdo de terceiros (só tema/gancho/formato, nunca vídeo/áudio original).

## Operating Context

- Roda 1x por dia, às 6h, via GitHub Actions (runner hospedado, sem depender da máquina do usuário ligada).
- O usuário recebe uma notificação push (Web Push/VAPID) quando a rodada diária termina.
- Abre o PWA quando quiser, de qualquer dispositivo, pra revisar os vídeos coletados e roteiros gerados antes de gravar/publicar seu próprio conteúdo.
- Volume: 10-15 vídeos processados por rodada.
- Instagram e Facebook são capturados manualmente pelo usuário (fora do pipeline automatizado nesta versão).

## Capabilities and Constraints

- Lista, por registro: plataforma de origem, link permanente do vídeo original, metadado extraído (tema, gancho, formato), roteiro gerado, timestamp de coleta.
- Nunca armazena o arquivo de vídeo em si — só o link. Vídeo do TikTok é baixado de forma transitória só para a chamada de análise da Gemini, e apagado logo em seguida.
- Sem autenticação nesta versão: acesso ao PWA é só por conhecer a URL (não divulgada publicamente). Migração para login real (Supabase Auth) é decisão futura, não deste momento.
- Sem push de terceiros (ex. OneSignal) — notificação via Web Push nativa (VAPID).
- Repositório do código é público no GitHub; nenhuma chave sensível (Gemini, Supabase, VAPID) fica no código — todas como GitHub Actions secrets.

## Brand Commitments

Nenhum ainda — projeto pessoal sem marca/identidade visual estabelecida.

## Evidence on Hand

Nenhum dado real ainda — o pipeline de coleta (tickets #2-#8) ainda não foi implementado, então o PWA (tickets #11/#12) não tem registros reais para exibir até essas dependências completarem. Nenhum conteúdo de exemplo deve ser fabricado como se fosse real.

## Product Principles

1. Nunca reaproveitar vídeo, áudio ou trecho de terceiros — só tema/gancho/formato como inspiração; o roteiro final é sempre original.
2. Automação sem esforço manual diário: o usuário só revisa, nunca precisa garimpar.
3. Infraestrutura gratuita e simples por padrão — só adiciona custo/complexidade (proxy pago, self-hosted runner, framework) quando o uso real justificar.
4. Falha parcial não derruba a rodada: um item bloqueado ou com erro é pulado, o resto do pipeline segue.
5. É uma ferramenta pessoal, não um produto — decisões priorizam simplicidade e uso próprio sobre polimento para terceiros.

## Accessibility & Inclusion

Nenhum requisito específico estabelecido — uso é pessoal e de único usuário.
