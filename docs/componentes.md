# Componentes, fontes e arquivos

Registro de tudo que entra no chassi além do MDF: o componente físico, de onde saiu cada medida usada no desenho e em que arquivo ela mora. Medida sem fonte não entra no `specs/modulos.json`; quando a fonte é fraca (foto, desenho sem cota), isso fica escrito aqui e no campo `fonte` da própria spec.

A linguagem construtiva (enforca-gato, dedos, camada dupla, gota de parede, pílula) está no repositório irmão, [dispensario-design-system](https://github.com/joshazze/dispensario-design-system).

## Interface do módulo biométrico

Os componentes de interface ficam no sub-painel `BSP` (240 x 560 mm, 1 lâmina), que vai atrás da janela de 180 x 500 da frente `B6E`. A regra de montagem é a mesma para todos: **só a parte saltada atravessa a chapa**, e a placa ou base do componente é parafusada por trás, encostada no MDF.

### Disposição e ergonomia

A disposição saiu de quem usa: profissional de enfermagem em pé, de qualquer altura, e também quem está sentado ou em cadeira de rodas. Ela separa o painel em duas zonas, **ver** em cima e **agir** embaixo, em vez de empilhar tudo num eixo só.

| zona | o que tem | centro na `BSP` (de baixo) | altura do piso* |
|---|---|---|---|
| ver | lente da câmera (direita) e LED (esquerda), na mesma linha | 445 | 1215 mm |
| ver | LCD, centrado | 400 | 1170 mm |
| agir | teclado (x = 84) e leitor (x = 166), lado a lado, na mesma altura | 140 | 910 mm |

\* Com o módulo pendurado com a base a **400 mm do piso**. A `BSP` fica centrada a 650 mm da base do módulo, então a altura do piso é 770 + a cota na `BSP`. É uma recomendação de instalação: se o módulo for pendurado mais alto ou mais baixo, tudo sobe ou desce junto.

Por que essas alturas:

- **Teclado e leitor entre 800 e 1000 mm.** É a faixa que a Resolução SEHAB/CPA nº 9 de 2003 (SP) dá para teclado e leitor de cartão, os comandos de coordenação fina. Ela atende quem está em pé e quem está em cadeira de rodas. O ADA põe 1220 mm como teto de alcance frontal. Uma pessoa alta se curva um pouco, como num caixa eletrônico.
- **Leitor ao lado do teclado, não abaixo.** Empilhados, um dos dois sairia da faixa. Lado a lado, a digital (o caminho normal) e a senha (o reserva) ficam no mesmo gesto. O leitor fica à direita, do lado da mão dominante da maioria.
- **LCD a ~1170 mm.** O 1602A é um STN com cone de visão estreito, e quem olha muito de cima perde contraste. A 1170 mm, quem tem 1,50 m (olho a ~1,40) vê a tela uns 20° abaixo do olho, a ~0,6 m de distância. Quem tem 1,85 m (olho a ~1,75) vê uns 45° abaixo. Quem está sentado (olho a ~1,20) vê de frente. Mais alto que isso, a tela fugiria de quem está sentado. O contraste do 1602A ainda se ajusta no trimpot.
- **Câmera na linha mais alta.** Quem lê a tela fica com o rosto virado pra lente, que está 45 mm acima e ao lado do LCD.
- **LED discreto.** É um ponto de 5 mm no canto de cima à esquerda, na linha da câmera, como a luz de uma webcam. Fica no campo de visão de quem lê a tela sem disputar atenção com o teclado.
- **Conjunto centrado na janela.** Sobram ~80 mm de respiro em cima e embaixo.

As cotas das peças ficam em `specs/modulos.json`. Lá, `x_mm` e `y_mm` são o centro da feição, vista de frente.

### Rebaixo por dentro: a `BSP` vai pra mesa ao contrário

O DevKit e a ESP32-CAM não atravessam a chapa: cada placa assenta num **rebaixo** gravado na face de dentro da `BSP`, no tamanho da placa mais 0,25 mm por lado. Pra gravar essa face, a `BSP` vai pra mesa **com a face de dentro pra cima**. Por isso a peça tem `"gravar_por_dentro": true` na spec, e o gerador espelha a `BSP` inteira no arquivo de corte. Na mesa, a câmera aparece à esquerda e o LED à direita. Isso está certo.

No LightBurn:

| camada do DXF | cor | modo | parâmetro | ordem |
|---|---|---|---|---|
| `MARCAÇÃO` | amarelo | Fill (gravação) | **150 mm/s × 80%**: o quadrado de baixo à direita da grade de gravação da matriz de MDF 3 mm de 27/10/2026 | primeiro |
| `CORTE` | vermelho | Linha | o de corte de sempre | depois |

A gravação vem antes do corte: com a peça já solta, o rebaixo sairia fora do lugar. A profundidade que 150/80 tira do MDF ainda **não foi medida**. Antes do corte oficial, medir com paquímetro o quadrado 150/80 da matriz.

### LCD 1602A (16 x 2)

| item | valor |
|---|---|
| peça do grupo | módulo 1602A Ver5.5, fundo azul, 16 pinos na borda longa, moldura metálica preta |
| placa | 80 x 36 mm |
| furos da placa | 4 furos em 75 x 31 entre centros |
| vão na chapa | 78 x 26 mm, com lingueta de 10 x 1 mm nas duas pontas curtas, centrado nos furos |
| furos na chapa | ⌀2,7 mm em 75 x 31, para M2 ou M2,5 |
| ponte mais fina | ~1,15 mm entre o vão e cada furo |

O passo dos furos, 75 x 31, é o mesmo nos três datasheets consultados. A moldura não é. Os datasheets dão uma moldura de 70,7 a 71,3 mm de comprimento, mas a foto da peça do grupo mostra a moldura passando cerca de 1 mm além da linha dos furos em cada ponta (uns 76 a 77 mm) e com cerca de 25 mm de altura, centrada nos furos. Valeu a peça: o vão foi dimensionado pela foto, com folga, e não pelos datasheets.

A lingueta existe porque a borda branca do backlight sai uns 1,5 mm de baixo da moldura numa das pontas. Ela foi posta nas duas pontas para o vão servir com a placa montada de qualquer lado.

Na face que encosta na chapa fica a solda dos 16 pinos. Se ela impedir a placa de assentar, uma arruela de cerca de 1 mm em cada parafuso resolve.

**Situação:** a foto não é medida. Antes do corte oficial, o vão passa por um corte de teste (ver Pendências).

### Teclado matricial 4x4 rígido

| item | valor |
|---|---|
| peça do grupo | teclado matricial 4x4 rígido, teclas de plástico, 16 teclas, conector de 10 pinos (anúncio da Smart Componentes) |
| base | 65 x 64 mm, com os 4 furos de fixação nos cantos |
| vão na chapa | 60,5 x 57,5 mm, cantos R4,25, centrado nos furos |
| furos na chapa | ⌀2,4 mm em 60 x 59, para M2 |
| ponte mais fina | ~0,95 mm entre o vão e cada furo |

O vendedor só informa 69 x 65 x 10 mm e "furos de fixação nas extremidades". A geometria vem do Multicomp MCAK1604NBWB, que tem o mesmo corpo (entalhe em cima, aba verde dos pinos embaixo, quatro furos nos cantos): recorte de painel de 60 x 57 com cantos R4, furos de ⌀2,3 em 60 x 59, base de 65 x 64. O Accord AK-1604, de onde o Multicomp deriva, informa o mesmo recorte de 60 x 57.

**Ponte abaixo do piso, aceita.** O próprio fabricante põe os furos colados no recorte, e no MDF de 3 mm sobra cerca de 1 mm entre cada furo e o vão. O piso do projeto é 1,5 mm (metade da espessura). A exceção foi aceita em 01/10/2026 e está declarada na spec da `BSP` (`ponte_aceita_mm` e `ponte_aceita_motivo`). O gerador imprime `EXCECAO DFM BSP` toda vez que roda, e um teste garante que a exceção vale só ali. Se uma ponte trincar, o parafuso ainda aperta a base pelo lado de fora do furo.

### Leitor biométrico Grow R307S

| item | valor |
|---|---|
| peça do grupo | Grow R307S, chip AS608, conector de 6 vias (3,3VT, TOUCH, RXD, TXD, GND, VCC) e USB de 4 |
| corpo | 44,1 de altura, seção de 20,1 x 23,5 mm (a placa de trás tem a mesma seção) |
| vidro | 15 x 11,19 mm na face de cima |
| vão na chapa | 20,6 x 24,0 mm (folga de 0,25 por lado) com 4 batentes de 2,0 x 4,0 nos cantos; meio livre de 16,6 |
| furos na chapa | 2 de ⌀3,2 a 38 mm entre centros, na altura do leitor, para M3 x 60 |
| presilha `BLR` | 56 x 40, janela de 17 x 26, 2 furos de ⌀3,2 a 38 |

As lojas dão quatro corpos diferentes para o R307S (52 x 20 x 22, 55 x 21 x 21,5, 46 x 21 x 23,5 e 48 x 24 x 20). Valeu o manual da própria Grow, que tem a única vista cotada: 44,1 x 20 x 23,5, com a placa de trás de 20,1 x 23,5. A foto da peça do grupo confere a placa quadrada com os 4 parafusos nos cantos.

O corpo não passa pelo vão. Os 4 batentes dos cantos ficam por fora da largura do vidro (15 mm, centrado) e seguram a face do leitor, que fica 3 mm abaixo da frente da chapa: o vão livre de 16,6 deixa o dedo chegar no vidro. Por trás, a presilha `BLR` aperta a placa do leitor contra os batentes. Ela apoia só nas faixas laterais da placa (~1,5 mm) e nas cabeças dos 4 parafusos dos cantos, e o conector e o cabo passam pela janela do meio. Montagem: 2 parafusos M3 x 60 entram pela frente da `BSP`, ganham uma porca encostada na chapa, atravessam a presilha e levam a porca que aperta. A conta do comprimento é 3 da `BSP` + 44,1 do corpo + 3 da presilha + porca.

### LED RGB de 5 mm (módulo KY-016)

| item | valor |
|---|---|
| peça do grupo | módulo KY-016, 4 pinos (GND, B, G, R) em barra de 90°, 2 furos de fixação, LED dobrado para fora da borda da placa |
| LED | 5 mm de corpo, aba da base de ~5,8 mm |
| furos na chapa | ⌀5,0 para o LED e 2 de ⌀2,4 a 10 mm entre centros para a placa, 3 mm ao lado do LED |

A placa fica deitada atrás da chapa, parafusada pelos 2 furos dela com M2, e o LED é endireitado a 90 graus da placa para atravessar o furo de ⌀5,0. Com 2 porcas M2 de espaçador em cada parafuso, a placa fica ~3 mm atrás da chapa e o LED salta ~2 mm na frente. A furação não aparece em nenhuma loja nem no datasheet da Joy-it: saiu da foto da peça do grupo em resolução cheia, usando como régua o passo de 2,54 mm da barra de pinos e conferindo pela aba de ~5,8 do LED. São 2 furos de ~2,5 a 10,0 mm entre centros, na borda do LED, numa placa de ~15 x 13. Por ser medida de foto, é a primeira coisa a conferir no corte de teste.

### ESP32 DevKitC (Eletrogate E33-003)

| item | valor |
|---|---|
| peça do grupo | ESP32 DevKitC S1, 38 pinos, módulo WROOM-32 |
| placa | 55 x 28 x 13 mm com pinos (anúncio da Eletrogate) |
| rebaixo | 28,5 x 55,5 mm, em pé, centro em x = 190 e y = 361,5 (vista de frente) |

A placa assenta com o módulo WROOM virado pra chapa e os pinos apontando pra dentro da caixa, onde entram os jumpers. O USB fica embaixo. Ela fica no canto de cima à direita, logo abaixo da ESP32-CAM, encostada na coluna dos parafusos da `BSP`. Não tem furo de fixação: quem segura a placa é o rebaixo.

### ESP32-CAM com OV2640 (Amazon B0CDJQV11V)

| item | valor |
|---|---|
| placa | 27 x 40,5 x 4,5 mm (±0,2), ficha Ai-Thinker ESP32-CAM V1.0 |
| rebaixo | 27,5 x 41,0 mm, em pé, centro em x = 190 e y = 435 |
| furo da câmera | ⌀12,5, centro em x = 190 e y = 445, **provisório** |

A placa assenta com a câmera virada pra chapa, e o módulo OV2640 atravessa o furo. O furo de 12,5 foi pensado pra passar um corpo quadrado de ~8,5 mm (diagonal ~12). Nenhuma loja nem a ficha da Ai-Thinker cota o módulo da câmera, nem a posição dele na placa. A spec supõe a lente a 10 mm do topo da placa. **Antes do corte, medir com paquímetro o corpo do OV2640 e a posição dele na placa** e trocar os dois números na spec.

### Ainda sem desenho

| componente | situação |
|---|---|
| tranca, 2 botões de porta | próximos recortes, no módulo armário |
| monitor touch | desejável, fora do protótipo por ora |

## Fixação e passagem de cabo

| componente | onde | medida usada | fonte |
|---|---|---|---|
| abraçadeira de nylon de 4,8 mm | une as lâminas e as faces (enforca-gato) | rasgo de 6,5 x 2,5 mm | largura da abraçadeira, com folga; ver o design system |
| prensa-cabo PG16 | tampa `BTR` / `ATR` | furo de ⌀22,5 | diâmetro nominal da rosca PG16 |
| parafuso da tampa do passa-fio | tampas ⌀90 sobre o passa-fio ⌀50 | 4 furos em quadrado de 51, piloto ⌀2,5 na parede e passante ⌀3,2 na tampa | M3 |
| parafuso do sub-painel e da placa de manutenção | `BSP` e `BPM` | piloto ⌀2,5 na face, passante ⌀3,2 na peça | M3 |
| parafuso de parede | fundo `B1` | gota com cabeça ⌀12, haste ⌀6,5, fenda de 10 mm para cima | ver o design system |

## Fontes

| fonte | o que deu | link |
|---|---|---|
| Tinsharp TC1602A-01T, p. 4 | furos 75 x 31, moldura 71,3 x 26,8 | [PDF (Adafruit)](https://cdn-shop.adafruit.com/datasheets/TC1602A-01T.pdf) |
| EONE 1602A-1 (Elecrow), p. 12 | furos 75,4 x 31,4 ⌀2,8, moldura 70,7 x 23,8, altura 7,0 | [PDF](https://www.elecrow.com/download/LCD1602.pdf) |
| HJ1602A, p. 2 | furos 75 x 31 ⌀2,5, moldura 70,8 x 23,8 | [PDF (Northwestern)](https://hades.mech.northwestern.edu/images/f/f7/LCD16x2_HJ1602A.pdf) |
| Waveshare LCD1602, p. 18 | placa 80 x 36, furos 75 x 31 | [PDF](https://www.waveshare.com/datasheet/LCD_en_PDF/LCD1602.pdf) |
| foto do KY-016 do grupo (IMG_7664) | furos de ~2,5 a 10,0 entre centros, placa de ~15 x 13 | foto de 07/10/2026, não publicada |
| foto do LCD do grupo | moldura ~76-77 x ~25, centrada; lingueta do backlight | foto tirada em 01/10/2026, não publicada |
| Multicomp MCAK1604NBWB, p. 2 | recorte 60 x 57 R4, furos ⌀2,3 em 60 x 59, base 65 x 64 | [PDF (Farnell)](https://www.farnell.com/datasheets/1662717.pdf) |
| Accord AK-1604 | recorte de painel 60 x 57, base 65 x 64 | [página do produto (TME)](https://www.tme.eu/en/details/kb1604-pnb/plastic-keypads/accord/ak-1604-n-bbw/) |
| Grow R307S User Manual, p. 2 | corpo 44,1 x 20 x 23,5, placa 20,1 x 23,5, vidro 15 x 11,19, pinagem | [PDF (Robu)](https://robu.in/wp-content/uploads/2024/08/R307S-fingerprint-module-user-manual.pdf) |
| Joy-it COM-KY016RGBLED | módulo com LED de 5 mm | [datasheet](https://www.joy-it.net/files/files/Produkte/COM-KY016-RGBLED/COM-KY016RGBLED-Datasheet.pdf) |
| fotos do R307S e do KY-016 do grupo | placa do leitor com 4 parafusos; LED dobrado para fora da placa | fotos tiradas em 07/10/2026, não publicadas |
| Smart Componentes | teclado 69 x 65 x 10, conector de 10 pinos | [loja](https://www.smartcomponentes.com/modulo-teclado-matricial-16-karet-teclas-alfanum-rico-4x4-arduino) |
| TabbedBoxMaker | matriz de juntas de dedos das seis faces | [GitHub](https://github.com/paulh-rnd/TabbedBoxMaker) |
| técnico do laboratório | perfil do DXF (AC1032, camada `CORTE`) | `perfis/` |

## Arquivos

| arquivo | o que é |
|---|---|
| `cortes/biometrico/interface-vaos.dxf` | **só os vãos e furos do LCD, do teclado, do leitor R307S, do LED e da câmera, mais os rebaixos das duas ESP32 na camada `MARCAÇÃO`**, sem o contorno da `BSP`, já espelhado, para cortar na peça que já foi cortada, com a face de dentro pra cima, alinhando à mão na mesa |
| `cortes/biometrico/interface-vaos.pdf` | o mesmo em escala 1:1, com 5 mm de margem: imprimir em 100% e pôr os componentes de cara para baixo em cima confere tudo sem paquímetro |
| `cortes/biometrico/modulo-biometrico-bloco3.dxf` | carga 3, que tem a `BSP` inteira já com os vãos |
| `specs/modulos.json` | peça `BSP`, campo `aberturas`: cada vão com `componente` e `fonte` |

```bash
python3 gerador.py --vaos BSP --nome biometrico/interface-vaos
```

## Pendências

1. **Corte de teste.** Cortar `interface-vaos.dxf` num retalho, encaixar o LCD, o teclado, o leitor, o LED e as duas ESP32 de verdade e conferir os vãos, os furos, os rebaixos e a solda dos pinos.
2. **Câmera e profundidade do rebaixo.** Medir o módulo OV2640 e a posição dele na placa, e a profundidade que 150 mm/s × 80% tira do MDF 3 mm.
3. **Corte oficial.** Só depois do teste: os vãos na `BSP` já cortada, ou a `BSP` nova da carga 3.
4. **Medida da moldura do LCD.** Se o teste mostrar folga demais ou de menos, trocar os pontos do vão na spec pela medida de paquímetro.
5. **Batentes do leitor.** Conferir no teste se os batentes de 2,0 mm pegam o corpo e se o dedo alcança o vidro 3 mm abaixo da frente.
