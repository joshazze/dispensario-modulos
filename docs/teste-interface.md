# Corte de teste da interface do biométrico

Antes de cortar a `BSP` de verdade, cada componente é testado num retalho do tamanho dele. Sai tudo numa chapa só, `cortes/biometrico/teste-interface.dxf` (146 x 257 mm, 12 peças). Ela tem um retalho por componente, com os mesmos vãos, furos e rebaixos da `BSP`, mais as peças pequenas (`BLR`, `BDB`, `BDP`, `BCB`, `BCP`) e um retalho com o alívio da `B6I`. Pra não desperdiçar, os retalhos têm a margem mínima do DFM (6 mm), as peças ficam a 2 mm umas das outras, o encaixe testa giro e largura até achar o menor retângulo, e o LED e o alívio são cortados **dentro do vão do teclado**, que ia virar refugo. Esses dois saem primeiro.

```bash
python3 gerador.py --teste BSP --nome biometrico/teste-interface
```

## O que levar

| item | quantidade |
|---|---|
| retalho de MDF 3 mm | pelo menos 160 x 270 mm |
| LCD 1602A, teclado 4x4, R307S, módulo KY-016, ESP32 DevKitC, ESP32-CAM | 1 de cada |
| o cabo micro USB que vai ficar instalado no DevKit | 1 |
| M3 x 60 + 4 porcas (leitor) | 2 |
| M3 x 16 + porca (DevKit, em cima) | 1 |
| M3 x 10 + porca (DevKit, embaixo, porca presa no bolso) | 2 |
| M3 x 20 + porca (ESP32-CAM) | 2 |
| M2 ou M2,5 + porca (LCD) | 4 |
| M2 + porca (teclado) | 4 |
| M2 + 3 porcas (LED: 2 de espaçador e 1 de aperto) | 2 |
| paquímetro e régua | |

## Na máquina

| camada do DXF | cor | modo | parâmetro | ordem |
|---|---|---|---|---|
| `MARCAÇÃO` | amarelo | Fill | 150 mm/s × 80% (quadrado de baixo à direita da grade de gravação da matriz de MDF 3 mm) | primeiro |
| `CORTE` | vermelho | Linha | o quadrado da grade de corte da matriz que atravessou limpo; sem ele, 26 mm/s × 65% (tabela do fabricante) | depois |

A face que fica pra cima na mesa é a **face de dentro**. Os rebaixos são gravados nela, e por isso o desenho sai espelhado em relação à vista de frente.

## O que conferir

1. **Profundidade do rebaixo:** medir com a haste de profundidade do paquímetro no retalho do DevKit. Esse número decide se a borda da placa pega na janela do berço.
2. **LCD:** a moldura passa pelo vão e a placa assenta sem a solda dos pinos encostar.
3. **Teclado:** o bloco passa pelo vão e os 4 furos batem com a base. A ponte de ~1 mm entre o vão e os furos aguenta.
4. **Leitor:** os 4 batentes seguram o corpo, o dedo alcança o vidro, e a `BLR` aperta nos M3 x 60.
5. **LED:** o LED passa pelo furo de 5,0 e os furos da placa batem. Essa furação veio de foto, então é a medida mais frágil.
6. **DevKit:** o módulo assenta no rebaixo em T, a placa entra no `BDB`, a `BDP` aperta, e as porcas ficam presas nos bolsos.
7. **USB do DevKit:** montar o retalho do alívio na frente do retalho do DevKit, com a gravação virada pra ele, como a `B6I` fica na frente da `BSP`. Plugar o cabo. Ele precisa entrar até o fim sem forçar a placa pra fora. Medir a espessura da capa do plugue.
8. **ESP32-CAM:** a câmera atravessa o furo de 12,5 e a placa entra no `BCB`. Medir o corpo do OV2640, a distância da lente até o topo da placa e a altura total da placa com a câmera. Esses números decidem o furo e o comprimento do parafuso.

## Resultados

| item | medido | ok? |
|---|---|---|
| profundidade do rebaixo 150/80 | | |
| parâmetro de corte usado | | |
| LCD | | |
| teclado | | |
| leitor + `BLR` | | |
| LED | | |
| DevKit + `BDB` + `BDP` | | |
| capa do plugue micro USB (espessura x largura) | | |
| corpo do OV2640 / lente até o topo da placa / altura total | | |
| ESP32-CAM + `BCB` + `BCP` | | |

O que não encaixar vira um número novo na `specs/modulos.json` (campo `fonte` dizendo que foi medido no teste), e só então sai a `BSP` oficial.
