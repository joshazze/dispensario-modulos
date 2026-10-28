# Handoff: corte da porta e das peças de gaveta do armário (28/10/2026)

Ler antes: `~/.claude/skills/laser/SKILL.md` e a memória `reference_mesa_laser_ibmec.md` (eCNC L-1210, layout até 1000 x 1000, origem Rear Right, fluxo Enviar no Mac + Start no painel).

## Onde está tudo

Repo `~/Projetos/dispensario-modulos`, worktree `~/Projetos/dispensario-porta-gaveta`, branch `feat/corte-porta-gaveta` (criada de origin/main, commit `4431043`, local, sem push). Pasta `cortes/armario/porta-gaveta/`:

| arquivo | o que é |
|---|---|
| `original/` | conteúdo intacto do zip `~/Downloads/Corte do armario.zip` (porta-corte, gaveta-pecas-corte, porta-medidas) |
| `chapa-1.dxf` | 945 x 880 mm: porta (frente) + base do batente + 3 encaixes na faixa à direita |
| `chapa-2.dxf` | 515 x 463 mm: fundo A + lateral B girada 90° |
| `previa.pdf` | uma página por chapa |
| `nest_armario.py` | regenera tudo: `python3 -I nest_armario.py original <saida>` |

Cópia solta dos mesmos arquivos em `~/Downloads/corte-armario-nesting/`.

Material MDF 3 mm. Camadas: CORTE vermelho, MARCACAO azul. Canto de baixo à esquerda em (0, 0), sem moldura, 5 mm entre peças. Conferido por script: contornos fechados, nada sobreposto, 137 entidades de origem preservadas. Não passou pelo `laser validate` (DXF veio de fora do gerador).

Gravações reduzidas a pedido do Josh: cada contorno de marcação (teclado, duas dobradiças) virou cantoneiras de 5 mm nos cantos; o que caía sobre a borda de corte saiu; o puxador ficou com um traço de 5 mm em cada ponta.

## Pendências, nesta ordem

1. **LightBurn está com o diálogo "Guardar projeto?" aberto** sobre o projeto `teste-interface` (modificado, não salvo). Regra do Josh: o que estiver no LightBurn sempre vai pro git, nunca descartar. Clicar Guardar; se pedir caminho, `~/Projetos/dispensario-modulos/cortes/biometrico/teste-interface.lbrn2`. Depois comitar esse `.lbrn2` na branch `feat/interface-ergonomia-esp32` daquele checkout (lá já está comitado o `teste-interface_backup.lbrn2`, `45e24c5`). O controle de tela estava preso por outra sessão; se ainda estiver, pedir ao Josh pra clicar.
2. Abrir `chapa-1.dxf` no LightBurn e conferir pela prévia. Abrir **uma chapa por vez** (abrir a 2 por cima sobrepõe as peças no canvas).
3. Acertar as camadas no LightBurn para MDF 3 mm. Tabela da máquina: corte 26 mm/s a 65%, marcação em linha 50 mm/s a 16%. Parâmetro já testado pelo Josh nos chaveiros: corte 4 mm/s a 50%. As camadas do projeto anterior (5/85 linha, 150/80 fill) não servem.
4. Salvar o projeto das chapas como `.lbrn2` dentro de `cortes/armario/porta-gaveta/` e comitar na branch `feat/corte-porta-gaveta`.

## Problemas em aberto no desenho (avisados ao Josh, sem resposta ainda)

1. **Lateral B**: a ranhura passante de 3,1 mm aberta na ponta direita deixa uma tira de 6 x ~460 mm presa só por 14 mm. Sai bamba e quebra. Saídas: ranhura fechada nas duas pontas, ou fundo com dentes em rasgos da lateral. Não cortar a chapa 2 sem decisão dele.
2. **Porta**: o arquivo diz que são duas chapas coladas e só veio a da frente. A de trás precisa dos mesmos vazados (janela LCD 71 x 24, furos M3, buzzer Ø8, câmera Ø15, rasgo do flat), senão tampa tudo. Perguntar se existe ou se gera a partir da frente.
3. Sem compensação de kerf: furos e janelas saem cerca de 0,1 a 0,2 mm maiores. Irrelevante para esses usos.

## Snapshot

`repos.md` do Cérebro já atualizado com a worktree e os dois commits. Ao mudar branch, mergear ou dar push, atualizar a linha do `dispensario-modulos` (sob `vault-lock.sh`).
