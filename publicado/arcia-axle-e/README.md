# Arcia Axle-E — carrinho utilitário autônomo para obra

Conceito de um carrinho elétrico 4x4 que transporta cascalho e entulho sozinho pelo canteiro — espera a
escavadeira encher a caçamba, leva a carga ao bota-fora, bascula e volta — apresentado como modelo 3D
interativo, simulação de obra jogável e ficha técnica gerada a partir do próprio modelo.

Site estático, sem backend e sem build: HTML + JavaScript (módulos ES) com Three.js carregado de CDN.

## Páginas

| Página | O que faz |
|---|---|
| `index.html` | Apresentação do projeto: modelo 3D girando, etapas, simulação embutida e ficha técnica |
| `modelo.html` | Visualizador 3D do carrinho (girar, aproximar, vistas prontas) |
| `simulacao.html` | Simulação de canteiro: dirigir, carregar com a escavadeira, descarregar no bota-fora, auto-execução |
| `ficha-tecnica.html` | Gera a ficha técnica (PNG 3000 × 4320) com vistas, cotas e especificações tiradas do modelo |

## Como abrir

Os módulos 3D precisam de servidor HTTP (abrir o arquivo com duplo clique não carrega o 3D). Na pasta do projeto:

```bash
python serve.py
```

Depois abra `http://localhost:8765/index.html`. O `serve.py` é um servidor estático sem cache; ele também
aceita `POST /salvar?nome=arquivo.png`, usado só para gravar a ficha técnica em `imagens/` durante o
desenvolvimento. Qualquer outro servidor estático (`npx serve .`) serve para navegar.

## Simulação

**Controles:** `W`/`S` acelerar e ré · `A`/`D` virar · `Espaço` freio · `E`/`Q` levantar e baixar a caçamba ·
`P` auto-execução · `L` faróis · `M` som · `C` câmera · `H` reiniciar. Arrastar o mouse gira a câmera.

**Ciclo autônomo** (botão azul ou `P`): ir à baia de carregamento → aguardar o sensor de peso marcar
≥ 170 kg estável por 1,5 s → levar ao bota-fora → bascular até esvaziar → recolher a caçamba → ré de 5 m →
repetir. Qualquer tecla de direção devolve o controle ao condutor.

**Segurança:** o sensor (LiDAR + câmera) analisa o corredor da trajetória à frente — ou atrás, em ré —
seguindo o arco definido pelo esterço. Compara a distância livre com a distância de parada e:

- alerta (amarelo, bipe intermitente) quando o obstáculo entra na zona de aviso;
- freia sozinho a 7 m/s² quando entra na distância de parada e impede arrancar em direção a ele.

A barra de status do carrinho mostra `SYS OK`, `AUTO`, `ALERTA` ou `FREIO`, e o display do painel traseiro
mostra velocidade, peso, ângulo da caçamba e bateria.

**Cenário:** prédio em construção com andaime e tela, grua, betoneira, contêineres de escritório,
estoques de material, barreiras, sinalização, tapume e seis trabalhadores com EPI — alguns cruzam as vias.
Os trabalhadores esperam o carrinho passar e, se ficarem bloqueados, se afastam para liberar a passagem.

## Estrutura

```
arcia-axle-e/
├── index.html · modelo.html · simulacao.html · ficha-tecnica.html
├── js/
│   ├── cart.js        modelo 3D procedural do carrinho (peças, materiais, display, faróis, cilindro)
│   ├── textures.js    texturas PBR geradas por código (pintura gasta, pneu, chapa xadrez, concreto…)
│   ├── assets.js      carregamento das texturas em imagem (textures/)
│   ├── site.js        cenário do canteiro + colisores
│   ├── excavator.js   escavadeira com braço por cinemática inversa de dois segmentos
│   ├── workers.js     trabalhadores com rotas, espera e desvio
│   ├── rocks.js       física das pedras, reciclagem e sensor de peso
│   ├── safety.js      sensor de colisão, alerta sonoro/visual e freio automático
│   └── autopilot.js   rota, seguidor de trajetória (pure pursuit) e máquina de estados do ciclo
├── textures/
│   ├── trabalhadores/ e escavadeira/   imagens geradas no Gemini (prompts em docs/)
│   └── prontas/                         recortes gerados por tools/preparar_texturas.py
├── imagens/           capturas da simulação e a ficha técnica exportada
├── docs/prompts-texturas.md            prompts usados para gerar as texturas
├── tools/preparar_texturas.py          recorta coletes e rostos, mede a cor da pele, tira o fundo verde do adesivo
└── serve.py           servidor local sem cache
```

Para regenerar os recortes depois de trocar uma textura: `python tools/preparar_texturas.py`
(requer `opencv-python` e `numpy`).

## Decisões técnicas

- **Modelo procedural em vez de malha importada.** O carrinho é montado em código (`cart.js`), então a
  simulação, o visualizador e a ficha técnica usam exatamente a mesma geometria — as cotas da ficha saem
  do modelo e não divergem dele. Custo: menos detalhe orgânico que uma malha modelada à mão.
- **Corredor de trajetória em arco.** A primeira versão previa o caminho como uma parábola e disparava
  alertas falsos em curvas fechadas; o cálculo pelo centro instantâneo de rotação eliminou isso.
- **Obstáculos como círculos.** Barato o bastante para checar centenas por quadro. Custo: cantos de
  objetos retangulares são aproximados.
- **Pedras que dormem.** Pedras paradas saem da integração, o que permite 260 pedras com colisão entre si.

## Validação feita

Simulação acelerada (sem renderizar) no navegador:

- 8 ciclos autônomos seguidos em 8,5 min simulados, sem travar; 1.406 kg entregues ao bota-fora;
- maior parada no trajeto: 1,6 s (esperando trabalhador);
- freio automático parando o carrinho a 0,7–1,0 m de trabalhadores que cruzaram a via;
- no modo manual, acelerando contra uma placa, parada a ~0,5 m dela com a ré liberada.

Não há suíte de testes automatizados: essas verificações foram rodadas manualmente por script no console.

## Limites

- É um **conceito em simulação**: não existe hardware, firmware nem integração com sensores reais.
- A física é simplificada (estilo arcade): sem inércia das pedras na caçamba, pneus sem atrito lateral,
  colisões só com o chão, a caçamba e os outros obstáculos aproximados por círculos.
- As especificações (200 kg, 70 V, 16 km/h manual / 10 km/h autônomo) são do conceito, não medidas.
- A bateria descarrega com a distância e trava em 3%; não há estação de recarga.
- O pool de 260 pedras é reciclado: o monte no bota-fora não cresce indefinidamente.
- A simulação pede teclado; não há controle por toque.
- Os hooks `window.__game` (pausar, avançar quadro a quadro, câmera) existem para depuração e testes.
