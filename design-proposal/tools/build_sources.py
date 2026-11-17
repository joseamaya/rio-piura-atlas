#!/usr/bin/env python3
"""Exporta data/sources.yml a un JS estático para el prototipo de Fuentes.

No es una fuente de verdad: la fuente de verdad sigue siendo data/sources.yml.
El archivo se usa solo en design-proposal/ para que el mockup funcione sin
servidor y sin dependencias.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "sources.yml"
OUT = ROOT / "design-proposal" / "assets" / "sources.js"

data = yaml.safe_load(SRC.read_text(encoding="utf-8"))
fuentes = data["fuentes"]

out = {
    "meta": data.get("meta", {}),
    "fuentes": fuentes,
    "resumen": {
        "total": len(fuentes),
        "disponible": sum(1 for f in fuentes if f.get("estado") == "disponible"),
        "por_solicitar": sum(1 for f in fuentes if f.get("estado") == "por_solicitar"),
        "por_verificar": sum(1 for f in fuentes if f.get("estado") == "por_verificar"),
    },
}
OUT.write_text(
    "window.SOURCES = " + json.dumps(out, ensure_ascii=False, indent=2) + ";\n",
    encoding="utf-8",
)
print(f"{OUT.relative_to(ROOT)}  {OUT.stat().st_size / 1024:.0f} kB  {len(fuentes)} fuentes")
