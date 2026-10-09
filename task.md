# 🚀 Antigravity + Claude Code: Workflow de Engenharia e Design (Padrão Sênior)

Este é o documento oficial de orquestração de projetos, estruturado para garantir rastreabilidade, isolamento de contexto e segurança na entrega. Ele elimina o colapso de informações entre IAs e protege a aplicação contra quebras por terceiros.

---

## <span style="color: #CC5500;">**Fase 1: O Cofre (Antigravity - Estratégia, Design e Handoff)**</span>

### <span style="color: #CC5500;">**Etapa 0: Discovery & Negócios**</span>
*   Prospecção de clientes e levantamento inicial de requisitos. (Atividade comercial, antes do projeto técnico iniciar).

### <span style="color: #CC5500;">**Etapa 0.5: Bootstrap do Repositório (O Cofre do Projeto)**</span>
*   Inicialização imediata do repositório Git local e sincronização com o GitHub remoto. **O GitHub é o backup oficial do projeto** — cobre código, documentação e diagramas. Ativos binários pesados (imagens em alta resolução, vídeos) devem usar Git LFS ou ficar fora do repo, versionando apenas os exports otimizados usados no código.
*   Criação da estrutura blindada:
    *   `ActiveContext.md` vazio — log vivo de cada sessão (o que foi feito, bloqueios, próximo passo).
    *   `AGENTS.md` (lido automaticamente pelo Claude Code) — o **Prompt Mestre** do projeto: contexto, guardrails e como rodar/testar. É atualizado só quando uma regra do projeto muda, não a cada sessão, para não virar ruído. É este arquivo que qualquer pessoa (ou IA) usa como ponto de partida para mexer no projeto sem quebrá-lo.
    *   `DESIGN.md` base.
    *   Pasta isolada `.agents/rules/`.
    *   Pasta `docs/` para diagramas de arquitetura da informação em Mermaid (`sitemap.md`, `user-flow.md`) — renderizados nativamente pelo GitHub, sem depender de ferramenta externa.
*   **Ambiente compartilhado:** Antigravity e Claude Code operam sobre a **mesma pasta de repositório local**. O Antigravity abre a pasta como uma "mission" (uma sessão de trabalho por app/feature) e, dentro dela, o Claude Code é executado via terminal integrado, apontando para o mesmo diretório. Os dois enxergam os mesmos arquivos e o mesmo `.git` — a troca de contexto entre as IAs acontece pelos arquivos (`DESIGN.md`, `ActiveContext.md`, `AGENTS.md`), não por uma integração direta entre elas.
*   A partir deste ponto, **todo o processo** é versionado em nuvem.

### <span style="color: #CC5500;">**Etapa 1: UX Research & Definição de Problema**</span>
*   Aplicação do framework Double Diamond.
*   Mapeamento de dores via scraping/análise de Reclame Aqui, Google Meu Negócio, etc.
*   Análise Competitiva de nicho.
*   Definição da Persona e construção da Proposta de Valor.
*   Matriz de Priorização de features para o MVP.

### <span style="color: #CC5500;">**Etapa 2: Arquitetura da Informação & UX Writing**</span>
*   Estruturação do Sitemap e mapeamento do User Flow completo, **redigidos diretamente em Mermaid** e salvos em `docs/sitemap.md` e `docs/user-flow.md`. O GitHub renderiza esses diagramas nativamente, mantendo-os versionados e legíveis tanto por humanos quanto pelas IAs, sem precisar de uma plataforma externa de diagramação.
*   Definição do Tom de Voz da marca.
*   Redação de cópias (textos) validadas para cada sessão do produto.

### <span style="color: #CC5500;">**Etapa 3: UI Design & Figma (Unificado)**</span>
*   Brainstorm visual e validação de acessibilidade (Matemática de Contraste WCAG) — o Figma continua sendo a **fonte de verdade para decisão de design** e a ferramenta de comunicação visual com o cliente.
*   Construção passo a passo do Design System no Figma (Grids estruturais, Botões, Ícones, Imagens, Tipografia, Paleta de Cores), componentizado para preservar a identidade visual do projeto.
*   Criação de Telas Responsivas para múltiplos breakpoints (Mobile, Tablet, Desktop).

### <span style="color: #CC5500;">**Etapa 4: O Handoff Algorítmico (O Cérebro da Operação)**</span>
*   Geração do `DESIGN.md` com YAML Frontmatter contendo os Tokens Técnicos extraídos do Figma (via Dev Mode ou plugin de tokens), evitando transcrição manual. **O `DESIGN.md` é a fonte de verdade que a IA lê** — o Figma é a fonte de verdade para a decisão visual; a consistência de identidade nas mãos da IA depende deste arquivo, não do Figma em si.
*   Redação de cenários de teste e regras de negócio no formato estruturado **Gherkin** (*Given-When-Then*).
*   Esta etapa é o combustível puro, sem ambiguidades, preparado especificamente para leitura de IAs.

---

## <span style="color: #CC5500;">**Fase 2: A Fábrica (Claude Code - Engenharia e QA Visual)**</span>

### <span style="color: #CC5500;">**Etapa 5: Brainstorm Dev & Setup de Infraestrutura**</span>
*   Claude Code lê o `DESIGN.md` e o `AGENTS.md` (leitura direta, já que compartilha a mesma pasta do Antigravity) e absorve o escopo.
*   Tradução dos Tokens do Figma para variáveis globais (CSS/Tailwind).
*   Definição da stack tecnológica definitiva e previsão de limitações de escalabilidade.

### <span style="color: #CC5500;">**Etapa 6: Backend & Banco de Dados**</span>
*   Desenvolvimento de APIs, rotas e estruturação do banco de dados aplicando arquitetura limpa.

### <span style="color: #CC5500;">**Etapa 7: Frontend Modular (Paradigma de Contêineres)**</span>
*   Criação de telas e componentes, rigorosamente mapeados pelo Figma.
*   <span style="color: #CC5500;">**Regra de Zero Trust (Worktrees):**</span> O desenvolvimento de cada nova interface acontece de forma isolada em um *Git Worktree* físico, jamais na branch `main`.
*   **Divergência de Design:** se o Claude Code identificar uma inconsistência ou inviabilidade técnica em relação ao Figma/`DESIGN.md`, o trabalho é pausado e a divergência é registrada no `ActiveContext.md` para retorno à Fase 1 (atualização do `DESIGN.md` e re-handoff), em vez de a IA decidir sozinha.

### <span style="color: #CC5500;">**Etapa 8: QA Visual & Rastreabilidade de Estado**</span>
*   Claude executa testes de interface (Playwright/Puppeteer) e gera evidências visuais dos estados.
*   Anexação das provas no arquivo `walkthrough.md`.
*   <span style="color: #CC5500;">**Validação Humana Obrigatória:**</span> O merge para a `main` só ocorre após a aprovação visual do Administrador (Gabe).

---

## <span style="color: #CC5500;">**Fase 3: A Entrega Comercial (Exportação e Proteção)**</span>

### <span style="color: #CC5500;">**Etapa 9: Exportação & AI Handoff Seguro**</span>
*   Limpeza do `README.md`, que funcionará apenas como um **Sitemap do Repositório** para desenvolvedores humanos.
*   <span style="color: #CC5500;">**Consolidação do `AGENTS.md` como `AI_MAINTENANCE_GUIDE.md`:**</span> como o `AGENTS.md` já foi mantido vivo desde a Etapa 0.5, esta etapa é uma revisão final, não uma criação do zero. O artefato final de alto valor para o cliente contém:
    *   **Prompt Mestre:** Para a IA do cliente iniciar o contexto.
    *   **Guardrails Arquiteturais:** O que é proibido alterar para não quebrar a aplicação.
    *   **Dicionário de Dependências:** Mapeamento de componentes e impactos visuais.
    *   **Padrão de Adição:** Regras estritas de como a nova IA deve criar funcionalidades mantendo o Design System intacto.

---

## <span style="color: #CC5500;">**O Rito Transversal (Executado no Fim de TODA Sessão)**</span>

Independentemente de quem esteja operando (Gabe, Gravy, ou Claude), ao fim de cada sessão de trabalho, os seguintes passos são **obrigatórios**:

1.  <span style="color: #CC5500;">**Atualizar `ActiveContext.md`:**</span> Registrar o que foi concluído, bloqueios, e qual a próxima etapa exata.
2.  <span style="color: #CC5500;">**Atualizar `AGENTS.md` (somente se necessário):**</span> Se alguma regra de negócio, guardrail ou padrão do projeto mudou nesta sessão, refletir aqui. Diferente do `ActiveContext.md`, este arquivo não é tocado toda sessão — só quando o "contrato" do projeto muda.
3.  <span style="color: #CC5500;">**Documentação Modular (Progressive Disclosure):**</span> Qualquer nova regra de negócio complexa deve ser salva isolada em `.agents/rules/[feature].md` com cabeçalho YAML. **Proibido poluir o root**.
4.  <span style="color: #CC5500;">**Commits Semânticos (Conventional Commits):**</span> Encapsular todo o trabalho em commits legíveis e tipados.
5.  <span style="color: #CC5500;">**Safe Backup (Push):**</span> Enviar o estado atual para o GitHub remoto, assegurando zero perda de dados.
