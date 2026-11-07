"""
villains.py — Definición modular de Villanos, Diálogos, Escenarios y Oleadas.

Permite al diseñador y al usuario ampliar o ajustar los personajes antagónicos,
la historia y las formaciones enemigas por oleada.
"""

from __future__ import annotations
from typing import Any


VILLAINS_DATA: dict[int, dict[str, Any]] = {
    1: {
        "name": "Comandante Colmillo",
        "title": "Líder de la Vanguardia Salvaje",
        "avatar": "🐗",
        "stage_id": "corral",
        "intro_dialogue": "¡Esta granja nos pertenece! ¡Entreguen el grano por las buenas o el barro correrá con sus lágrimas!",
        "victory_dialogue": "¡Malditos animales domésticos! Esto recién empieza...",
    },
    2: {
        "name": "El Cuervo Rapaz",
        "title": "Ojo de la Carroña",
        "avatar": "🦅",
        "stage_id": "corral",
        "intro_dialogue": "Creen que una victoria de suerte los salvará. No dejaré ni una sola semilla intacta en sus comederos.",
        "victory_dialogue": "¡Mis plumas! ¡Volveré con refuerzos de la bandada!",
    },
    3: {
        "name": "Capataz Bramido",
        "title": "Tirano del Corral Principal",
        "avatar": "🐂",
        "stage_id": "corral",
        "intro_dialogue": "¡Nadie escapa de mi yugo! Demuestren si su rebeldía tiene la fuerza para doblar mis cuernos de acero.",
        "victory_dialogue": "¡Imposible! ¡El corral... ha caído! Pero en los huertos los esperará su fin...",
    },
    4: {
        "name": "Sombra Calavera",
        "title": "Acechador del Huerto",
        "avatar": "🎃",
        "stage_id": "huerto",
        "intro_dialogue": "Las calabazas guardan oscuros secretos. Pasen si se atreven a pisar la tierra podrida.",
        "victory_dialogue": "¡Agh! El sol no brillará para siempre sobre su cosecha...",
    },
    5: {
        "name": "Pato Mortífero",
        "title": "Artillero de la Ciénaga",
        "avatar": "🦆",
        "stage_id": "huerto",
        "intro_dialogue": "¡Cuaaack! ¿Oyen ese zumbido en el aire? Es la lluvia de metralla que acabará con su rebelión.",
        "victory_dialogue": "¡Mis bombarderos averiados! ¡A las trincheras del huerto!",
    },
    6: {
        "name": "El Espantajo Mayor",
        "title": "Señor de la Paja Maldita",
        "avatar": "🌾",
        "stage_id": "huerto",
        "intro_dialogue": "Los cuervos me temen, y ustedes temblarán ante mi hechizo de inmovilidad. ¡De aquí no pasarán!",
        "victory_dialogue": "¡Mi paja se desmorona...! Aún les queda enfrentar las máquinas del Silo Oxidado...",
    },
    7: {
        "name": "Barón Chatarra",
        "title": "Ingeniero del Óxido",
        "avatar": "⚙️",
        "stage_id": "silo",
        "intro_dialogue": "Bienvenidos al territorio de la maquinaria pesada. Su carne de corral no resistirá el metal.",
        "victory_dialogue": "¡Mis pistones se sobrecalentaron! ¡General, active las defensas!",
    },
    8: {
        "name": "General Garra de Hierro",
        "title": "Comandante de Élite Mecanizada",
        "avatar": "🐺",
        "stage_id": "silo",
        "intro_dialogue": "Disciplina y potencia bélica. No tienen la menor oportunidad frente a mi escuadrón táctico.",
        "victory_dialogue": "¡Retirada estratégica hacia la cima del Silo! ¡El Supremo se encargará de ustedes!",
    },
    9: {
        "name": "Titán Oxidado",
        "title": "Coloso de Grano y Chapa",
        "avatar": "🛡️",
        "stage_id": "silo",
        "intro_dialogue": "¡CRUNCH! Pisadas que hacen temblar la tierra. Destruiré su esperanza grano por grano.",
        "victory_dialogue": "¡Sistemas críticos fallando! ¡El amo los espera en la cima!",
    },
    10: {
        "name": "Supremo Usurpador",
        "title": "Amo del Silo y Rey del Despojo",
        "avatar": "👑",
        "stage_id": "silo",
        "intro_dialogue": "Han llegado lejos, insignificantes granjeros. Pero toda esta cosecha y sus vidas ahora me pertenecen. ¡A pelear!",
        "victory_dialogue": "¡Nooooo! ¡La granja es libre... por ahora!",
    },
}

EXPANDED_WAVE_COMPOSITIONS: dict[int, list[dict[str, Any]]] = {
    1: [
        {"id": "E01", "unit_id": "U02", "level": 1, "position": 4},
        {"id": "E02", "unit_id": "U06", "level": 1, "position": 5},
    ],
    2: [
        {"id": "E01", "unit_id": "U02", "level": 1, "position": 3},
        {"id": "E02", "unit_id": "U03", "level": 1, "position": 4},
        {"id": "E03", "unit_id": "U06", "level": 1, "position": 5},
    ],
    3: [
        {"id": "E01", "unit_id": "U01", "level": 2, "position": 3},
        {"id": "E02", "unit_id": "U02", "level": 2, "position": 4},
        {"id": "E03", "unit_id": "U07", "level": 1, "position": 5},
        {"id": "E04", "unit_id": "U06", "level": 2, "position": 8},
    ],
    4: [
        {"id": "E01", "unit_id": "U01", "level": 1, "position": 1},
        {"id": "E02", "unit_id": "U04", "level": 1, "position": 4},
        {"id": "E03", "unit_id": "U08", "level": 1, "position": 7},
    ],
    5: [
        {"id": "E01", "unit_id": "U02", "level": 2, "position": 1},
        {"id": "E02", "unit_id": "U05", "level": 1, "position": 4},
        {"id": "E03", "unit_id": "U03", "level": 2, "position": 6},
        {"id": "E04", "unit_id": "U06", "level": 2, "position": 8},
    ],
    6: [
        {"id": "E01", "unit_id": "U02", "level": 2, "position": 0},
        {"id": "E02", "unit_id": "U01", "level": 2, "position": 2},
        {"id": "E03", "unit_id": "U08", "level": 2, "position": 4},
        {"id": "E04", "unit_id": "U04", "level": 2, "position": 7},
        {"id": "E05", "unit_id": "U07", "level": 2, "position": 8},
    ],
    7: [
        {"id": "E01", "unit_id": "U01", "level": 2, "position": 1},
        {"id": "E02", "unit_id": "U02", "level": 2, "position": 4},
        {"id": "E03", "unit_id": "U05", "level": 2, "position": 6},
        {"id": "E04", "unit_id": "U07", "level": 2, "position": 8},
    ],
    8: [
        {"id": "E01", "unit_id": "U04", "level": 2, "position": 0},
        {"id": "E02", "unit_id": "U02", "level": 2, "position": 3},
        {"id": "E03", "unit_id": "U05", "level": 2, "position": 4},
        {"id": "E04", "unit_id": "U03", "level": 2, "position": 6},
        {"id": "E05", "unit_id": "U06", "level": 2, "position": 7},
    ],
    9: [
        {"id": "E01", "unit_id": "U01", "level": 3, "position": 1},
        {"id": "E02", "unit_id": "U02", "level": 2, "position": 3},
        {"id": "E03", "unit_id": "U08", "level": 2, "position": 4},
        {"id": "E04", "unit_id": "U06", "level": 2, "position": 5},
        {"id": "E05", "unit_id": "U07", "level": 2, "position": 7},
    ],
    10: [
        {"id": "E01", "unit_id": "U02", "level": 3, "position": 1},
        {"id": "E02", "unit_id": "U03", "level": 3, "position": 3},
        {"id": "E03", "unit_id": "U08", "level": 2, "position": 4},
        {"id": "E04", "unit_id": "U07", "level": 2, "position": 5},
        {"id": "E05", "unit_id": "U06", "level": 3, "position": 7},
    ],
}
