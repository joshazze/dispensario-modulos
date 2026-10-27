# Componentes, fontes e arquivos

Registro de tudo que entra no chassi além do MDF: o componente físico, de onde saiu cada medida usada no desenho e em que arquivo ela mora. Medida sem fonte não entra no `specs/modulos.json`; quando a fonte é fraca (foto, desenho sem cota), isso fica escrito aqui e no campo `fonte` da própria spec.

A linguagem construtiva (enforca-gato, dedos, camada dupla, gota de parede, pílula) está no repositório irmão, [dispensario-design-system](https://github.com/joshazze/dispensario-design-system).

## Interface do módulo biométrico

Os componentes de interface ficam no sub-painel `BSP` (240 x 560 mm, 1 lâmina), que vai atrás da janela de 180 x 500 da frente `B6E`. A regra de montagem é a mesma para todos: **só a parte saltada atravessa a chapa**, e a placa ou base do componente é parafusada por trás, encostada no MDF.

Todos ficam centrados na largura da `BSP`. O LCD tem o centro dos furos a 480 mm da base da peça e o teclado a 380, então o LCD fica 100 mm acima do teclado. O leitor R307S está a 300 e o LED a 265, **em posição provisória**: a ordem do projeto é desenhar o recorte de cada componente primeiro e só depois organizar todos nos módulos.

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
| vão na chapa | 20,6 x 24,0 mm, cantos vivos, folga de 0,25 por lado |
| furos na chapa | nenhum |

As lojas dão quatro corpos diferentes para o R307S (52 x 20 x 22, 55 x 21 x 21,5, 46 x 21 x 23,5 e 48 x 24 x 20). Valeu o manual da própria Grow, que tem a única vista cotada: 44,1 x 20 x 23,5, com a placa de trás de 20,1 x 23,5. A foto da peça do grupo confere a placa quadrada com os 4 parafusos nos cantos.

O corpo atravessa a chapa inteiro, com o vidro rente à frente. Ele não tem aba nem furo livre (os 4 parafusos dos cantos já prendem a placa no corpo), então **a retenção fica por trás e ainda não está desenhada**: entra quando os componentes forem organizados no módulo. O manual mostra um entalhe de 1,5 mm de cada lado do corpo, a 22,9 mm do topo, que pode servir de trava para esse suporte.

### LED RGB de 5 mm (módulo KY-016)

| item | valor |
|---|---|
| peça do grupo | módulo KY-016, 4 pinos (GND, B, G, R) em barra de 90°, 2 furos de fixação, LED dobrado para fora da borda da placa |
| LED | 5 mm de corpo, aba da base de ~5,8 mm |
| furo na chapa | ⌀5,0 |

O LED entra por trás e para na chapa pela aba da base. Como ele já sai dobrado para fora da borda, a placa fica de pé atrás da chapa, presa pelos terminais, e os 2 furos dela não são usados. O furo tem o diâmetro nominal do LED porque o laser abre o furo sozinho (kerf estimado em 0,18): se sair frouxo, uma gota de cola quente resolve. A medida do furo é a primeira coisa a conferir no corte de teste.

### Ainda sem desenho

| componente | situação |
|---|---|
| tranca, 2 botões de porta, ESP32 DevKitC, ESP32-CAM | próximos recortes |
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
| `cortes/biometrico/interface-vaos.dxf` | **só os vãos e furos do LCD, do teclado, do leitor R307S e do LED**, sem o contorno da `BSP`, para cortar na peça que já foi cortada, alinhando à mão na mesa |
| `cortes/biometrico/interface-vaos.pdf` | o mesmo em escala 1:1, com 5 mm de margem: imprimir em 100% e pôr os componentes de cara para baixo em cima confere tudo sem paquímetro |
| `cortes/biometrico/modulo-biometrico-bloco3.dxf` | carga 3, que tem a `BSP` inteira já com os vãos |
| `specs/modulos.json` | peça `BSP`, campo `aberturas`: cada vão com `componente` e `fonte` |

```bash
python3 gerador.py --vaos BSP --nome biometrico/interface-vaos
```

## Pendências

1. **Corte de teste.** Cortar `interface-vaos.dxf` num retalho, encaixar o LCD, o teclado, o leitor e o LED de verdade e conferir os vãos, os furos e a solda dos pinos.
2. **Corte oficial.** Só depois do teste: os vãos na `BSP` já cortada, ou a `BSP` nova da carga 3.
3. **Medida da moldura do LCD.** Se o teste mostrar folga demais ou de menos, trocar os pontos do vão na spec pela medida de paquímetro.
4. **Retenção do leitor R307S.** Suporte por trás da `BSP`, desenhado quando os componentes forem organizados nos módulos.
