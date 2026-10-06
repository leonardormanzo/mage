# Prompts de textura (Gemini) — trabalhadores e escavadeira

Os modelos 3D são feitos de peças simples (caixas, cilindros), então as texturas são de dois tipos:

- **Material contínuo (tileable):** um retalho que se repete sem emenda e cobre a peça inteira.
- **Painel/decalque:** uma imagem única aplicada numa face (frente do colete, adesivo, logo).

## Como gerar

1. Cole o **prompt** de cada item no Gemini e acrescente a **regra comum** do grupo no final.
2. Gere em **1:1 (quadrado)**, na maior resolução disponível (de preferência 1024×1024 ou mais).
3. Salve em PNG com o **nome exato** indicado, nas pastas:
   - `textures/trabalhadores/`
   - `textures/escavadeira/`
4. Para decalques com fundo verde (#00FF00), eu removo o fundo ao aplicar.

Depois é só me avisar que eu ligo cada arquivo na peça certa do modelo.

---

## Regras comuns (cole no fim de cada prompt)

**Para materiais contínuos (tileable):**

> seamless tileable texture, edges wrap perfectly on all four sides, orthographic top-down flat scan, perfectly even diffuse lighting, no shadows, no highlights, no perspective, no vignette, no text, no watermark, photorealistic PBR albedo map, square 1:1, high detail

**Para painéis e decalques:**

> flat orthographic front view, perfectly even diffuse lighting, no shadows, no perspective, centered, fills the frame edge to edge, photorealistic, square 1:1, no watermark

---

## 1. Trabalhadores (EPI)

| Arquivo | Onde vai | Tipo |
|---|---|---|
| `colete_frente.png` | frente do tronco | painel |
| `colete_costas.png` | costas do tronco | painel |
| `manga_camisa.png` | braços | contínuo |
| `calca_trabalho.png` | pernas | contínuo |
| `bota_couro.png` | botas | contínuo |
| `capacete_plastico.png` | capacete | contínuo |
| `capacete_adesivo.png` | adesivo frontal do capacete | decalque |
| `rosto_1.png` a `rosto_4.png` | rosto (frente da cabeça) | painel |

### colete_frente.png — painel
> Front view of a high-visibility fluorescent orange safety vest laid perfectly flat, polyester mesh fabric texture, a center zipper running vertically, two horizontal silver retroreflective stripes across the chest and the waist, a small black embroidered "TERRA-BOTICS" logo on the left chest, slight wear and light dust from a construction site. Only the vest fabric fills the image, no background, no mannequin, no person.

### colete_costas.png — painel
> Back view of the same fluorescent orange high-visibility safety vest laid perfectly flat, polyester mesh fabric, two horizontal silver retroreflective stripes across the back, large black screen-printed text "TERRA-BOTICS" across the upper back and smaller text "SEGURANÇA DO TRABALHO" below it, light dust and wear. Only the vest fabric fills the image, no background, no person.

### manga_camisa.png — contínuo
> Close-up of a dark navy blue cotton twill work shirt fabric, visible diagonal weave, slightly faded, subtle dust stains from a construction site.

### calca_trabalho.png — contínuo
> Close-up of dark blue heavy-duty work trousers denim fabric, visible twill weave, slightly worn and faded, light gray concrete dust smudges.

### bota_couro.png — contínuo
> Close-up of brown oiled leather from safety work boots, natural grain, creases, scuffs and dried mud specks.

### capacete_plastico.png — contínuo
> Close-up of glossy white ABS plastic surface of a construction hard hat, very subtle micro scratches and faint dust, almost uniform white.

### capacete_adesivo.png — decalque
> A small rectangular vinyl sticker for a hard hat: black "TERRA-BOTICS" logo text with a simple stylized wheel icon on a white background with rounded corners, isolated on a solid pure green #00FF00 background.

### rosto_1.png … rosto_4.png — painel (gere 4 variações)
> Frontal flat texture of an adult construction worker's face, neutral expression, looking straight ahead, symmetrical, framed from the top of the forehead to the chin and from ear to ear, even flat lighting, natural skin texture, light sweat and a little dust, no hat, no glasses. Variation: [1: Brazilian man, medium-brown skin, short dark beard] [2: Brazilian woman, light-brown skin, hair tied back] [3: Brazilian man, dark skin, clean-shaven] [4: Brazilian man, fair skin, short mustache].

---

## 2. Escavadeira hidráulica (esteira)

> O modelo da cena é uma **escavadeira hidráulica de esteira**, não uma retroescavadeira (pá carregadeira na frente, braço atrás e rodas). Os prompts abaixo servem para a escavadeira atual. Se quiser uma retroescavadeira de verdade, eu modelo e adapto os prompts.

| Arquivo | Onde vai | Tipo |
|---|---|---|
| `pintura_amarela.png` | cabine, lança, braço | contínuo |
| `contrapeso_cinza.png` | contrapeso e chassi inferior | contínuo |
| `esteira_sapatas.png` | esteiras | contínuo |
| `cacamba_aco.png` | caçamba (concha) | contínuo |
| `capo_grade.png` | tampa do motor (lateral) | painel |
| `cabine_lateral.png` | lateral da cabine do operador | painel |
| `logo_terrabotics.png` | lateral da cabine/lança | decalque |
| `adesivos_seguranca.png` | perto do contrapeso | decalque |
| `sujeira_lama.png` | parte baixa (sobreposição) | contínuo |

### pintura_amarela.png — contínuo
> Close-up of heavy construction equipment painted steel, saturated industrial yellow enamel paint, slightly faded by sun, small chipped spots showing dark gray primer and bare metal, light dust layer, faint oil streaks, hairline scratches.

### contrapeso_cinza.png — contínuo
> Close-up of dark charcoal gray powder-coated cast steel from an excavator counterweight, rough cast texture, scuffs, dust and grease marks, a few rust-tinted scratches.

### esteira_sapatas.png — contínuo
> Top-down view of steel excavator track shoes (track pads) in a straight continuous row running vertically, each pad with two raised grousers and bolt heads, worn dark steel with packed brown mud and small stones between the pads, tileable seamlessly along the vertical direction.

### cacamba_aco.png — contínuo
> Close-up of the inside wear surface of an excavator digging bucket, abraded bare steel polished by gravel, deep scratches in one direction, patches of orange-brown rust, dried mud and gravel dust in the corners.

### capo_grade.png — painel
> Flat front view of an excavator engine side cover panel painted industrial yellow, with a rectangular ventilation grille of horizontal black louvers in the center, four bolt heads at the corners, a small black handle, light dust and paint chips.

### cabine_lateral.png — painel
> Flat side view of an excavator operator cab side, industrial yellow painted steel frame surrounding a large tinted dark glass window with a subtle sky reflection, a black rubber window seal, a small grab handle, light dust on the frame.

### logo_terrabotics.png — decalque
> A wide horizontal vinyl decal reading "TERRA-BOTICS" in bold black condensed industrial lettering, with a thin black underline stripe and a small "TB-220" model tag on the right, isolated on a solid pure green #00FF00 background. Wide 4:1 composition centered in a square image.

### adesivos_seguranca.png — decalque
> A set of three industrial safety warning stickers arranged in a row: a yellow triangle with a black crushing-hazard pictogram, a yellow sticker with text "PERIGO — RAIO DE GIRO", and a yellow sticker with text "MANTENHA DISTÂNCIA 5 m", black borders, isolated on a solid pure green #00FF00 background.

### sujeira_lama.png — contínuo
> Close-up of dried brown construction-site mud splatter and dust on a flat surface, irregular splashes thinning out, natural earthy browns, isolated on a solid pure white background.
