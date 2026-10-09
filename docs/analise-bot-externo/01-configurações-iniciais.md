# 01 - Configurações Iniciais

- Vídeo: https://www.youtube.com/watch?v=RSdrUMdtPqw
- Modelo: gemini-3.8-flash

---

## Resumo
O vídeo aborda exclusivamente a etapa preparatória pré-execução do bot "Pokemon Aliiance V3" (PokeTibia Bot) no sistema operacional Windows 10. O apresentador demonstra o ajuste obrigatório da escala de exibição do Windows para 100% para garantir o correto funcionamento da ferramenta. Em seguida, realiza a descompactação do arquivo do programa via WinRAR na Área de Trabalho e exibe a estrutura inicial de pastas e executáveis que compõem o bot.

---

## Funcionalidades

### 1. Configuração de Escala e Layout do Windows
1. **Nome da funcionalidade/aba/módulo:**
   * Configuração de Escala e Layout do Sistema (Windows 10 - Configurações de Tela).
2. **O que ela faz e como o usuário configura:**
   * **Objetivo:** Garante que a renderização de elementos gráficos e coordenadas na tela permaneça em proporção 1:1 (sem distorção de DPI).
   * **Procedimento executado:** 
     * O usuário clica com o botão direito na Área de Trabalho e seleciona "Configurações de exibição".
     * Na janela "Tela", localiza a seção **Ajustar escala e layout** ("Alterar o tamanho do texto, dos aplicativos e de outros itens").
     * Abre a lista suspensa com as opções visíveis: `100% (Recomendado)`, `125%`, `150%` e `175%`.
     * Define obrigatoriamente a opção em **100%**.
3. **Como parece funcionar por baixo:**
   * **Dito no vídeo:** O narrador afirma expressamente que a escala precisa estar em 100%, alertando que caso esteja acima disso (como 125%), "o bot não roda tão bem".
   * **Inferência técnica:** Bots externos de PokeTibia desse tipo costumam operar via reconhecimento de imagem/padrão de pixel (ImageSearch / pixel scanning) e emulação de mouse/teclado com coordenadas estáticas ou relativas. Quando a escala de DPI do Windows está acima de 100%, o sistema aplica interpolação gráfica e deslocamento de coordenadas, o que quebra a precisão dos cliques e a correspondência exata de bitmaps/templates.
4. **Limitações, bugs, dicas ou reclamações mencionadas:**
   * O narrador destaca uma dica específica para usuários de **notebooks**, informando que esses aparelhos frequentemente vêm configurados de fábrica com escala superior a 100%, necessitando de verificação obrigatória.
5. **Minutagem:**
   * `00:06` a `00:25`.

---

### 2. Descompactação e Inicialização do Pacote
1. **Nome da funcionalidade/aba/módulo:**
   * Extração do arquivo compactado `Poketibia Bot.rar`.
2. **O que ela faz e como o usuário configura:**
   * **Procedimento:** O usuário clica com o botão direito sobre o arquivo compactado `Poketibia Bot.rar` na Área de Trabalho e aciona o menu de contexto do WinRAR na opção `Extrair para Poketibia Bot\`.
   * Uma nova pasta homônima é gerada no desktop contendo os arquivos do software.
3. **Como parece funcionar por baixo:**
   * **Dito no vídeo:** É o procedimento padrão para disponibilizar os arquivos para uso.
   * **Inferência técnica:** Descompactação de binários portáteis sem necessidade de instalador MSI/Setup dedicado.
4. **Limitações, bugs, dicas ou reclamações mencionadas:**
   * Nenhuma falha apontada; apenas a indicação de que o bot fica localizado dentro do diretório extraído.
5. **Minutagem:**
   * `00:26` a `00:35`.

---

## Detalhes de interface

Neste vídeo específico, a interface gráfica interna do próprio bot ainda não é aberta; o vídeo foca no ambiente do sistema operacional e na estrutura de arquivos:

1. **Janela de Configurações do Windows 10 (`00:10` - `00:25`):**
   * Tela de configurações nativa com menu lateral esquerdo (Vídeo, Notificações e ações, Assistente de foco, Energia e suspensão, etc.).
   * Seção central "Tela" exibindo:
     * *Luz noturna* (desativado).
     * *Windows HD Color*.
     * *Ajustar escala e layout*: Dropdown ativo mostrando 100%, 125%, 150%, 175%.
     * *Resolução de tela*: Dropdown visível indicando `1920 x 1080 (Recomendado)`.
     * *Orientação de tela*: Paisagem.

2. **Estrutura de Arquivos no Windows Explorer (`00:32` - `00:35`):**
   * Caminho aberto: `Área de Trabalho > Poketibia Bot`.
   * Itens visíveis no diretório:
     * Pasta: `Configurações de imagem` (Data: 06/08/2019).
     * Pasta: `Config` (Data: 06/08/2019).
     * Arquivo Executável: `Simply1` (Aplicativo, 172 KB, 06/08/2019).
     * Arquivo Executável: `Simply2` (Aplicativo, 172 KB, 06/08/2019).
     * Arquivo Executável: `Simply3` (Aplicativo, 172 KB, 06/08/2019).

---

## Observações técnicas e inferências

* **Mecanismo de Detecção e Automação:** A presença da pasta `Configurações de imagem` combinada com a exigência estrita de dimensionamento em 100% reforça que o bot se baseia fortemente em comparação de imagens/bitmaps capturados da tela (como caixas de vida, barras de Pokémon, botões de ação e inventário).
* **Múltiplos Executáveis (`Simply1`, `Simply2`, `Simply3`):** 
  * A nomenclatura sequencial com tamanho uniforme (172 KB cada) é comum em scripts compilados (por exemplo, via AutoIt ou AutoHotkey) desenhados para suportar múltiplos clientes/telas abertas simultaneamente (MC - Multi-Client) ou segmentados por abas/instâncias.
* **Formatos de Configuração:** A existência de um diretório exclusivo chamado `Config` indica separação entre os dados de perfil/hotkeys do usuário e as imagens de referência padrão do sistema (`Configurações de imagem`).
