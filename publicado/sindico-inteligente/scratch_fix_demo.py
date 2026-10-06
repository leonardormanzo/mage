import pathlib
p = pathlib.Path(r"c:\Users\Leonardo Manzo\Desktop\projetos engennr\publicado\sindico-inteligente\demo-api.js")
text = p.read_text(encoding="utf-8")
text = text.replace(
    '  document.addEventListener("DOMContentLoaded", () => {\n    setTimeout(() => window.dispatchEvent(new Event("pywebviewready")), 100);\n  });',
    '  const dispatchReady = () => window.dispatchEvent(new Event("pywebviewready"));\n  if (document.readyState === "loading") {\n    document.addEventListener("DOMContentLoaded", () => setTimeout(dispatchReady, 100));\n  } else {\n    setTimeout(dispatchReady, 100);\n  }'
)
p.write_text(text, encoding="utf-8")
