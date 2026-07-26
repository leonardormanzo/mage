# Checklist de Obra

Protótipo de interface para checklist de obra com comparação de fotos "antes/depois"
de reparos. Registra o nome da obra, cria o checklist item a item, e para cada item
guarda a foto de antes e a foto de depois do reparo — o app gera automaticamente um
comparativo pronto para compartilhar com o cliente.

**Página única (HTML/CSS/JS), sem backend** — o estado vive apenas na sessão do
navegador e não persiste ao recarregar a página.

## Como abrir

Abra `index.html` diretamente no navegador, ou sirva a pasta com qualquer servidor
estático (ex: `npx serve .`).

## Fluxo

1. Preencha o nome da obra e crie o checklist.
2. Para cada item, registre a foto de "antes" e, após o reparo, a foto de "depois".
3. O app monta o comparativo automaticamente e permite compartilhar com o cliente.

## Falta para terminar

Persistência real dos dados (hoje some ao recarregar) e exportação/compartilhamento
do comparativo (ex: PDF ou link) em vez de só exibir na tela.
