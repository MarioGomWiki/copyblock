#!/usr/bin/env bash

python copyblock.py --comment-pattern 'p2p proxy' --block-reason "{{Proxy P2P bloqueado}}. Visita [[Wikipedia:Proxies abiertos|la página informativa]] si estás afectado. <!-- Proxy P2P confirmado por API -->" --really-run
python copyyblock.py --comment-pattern 'blocked proxy' --block-reason "{{proxy bloqueado}}. Visita [[Wikipedia:Proxies abiertos|la página informativa]] si estás afectado. <!-- Bloqueo hecho por bot -->" --really-run
python copyblock.py --comment-pattern 'blocked proxy' --ranges --block-reason "{{proxy bloqueado}}. Visita [[Wikipedia:Proxies abiertos|la página informativa]] si estás afectado. <!-- Bloqueo hecho por bot -->" --really-run
python copyblock.py --comment-pattern webhost --ranges --block-reason "{{Webhost bloqueado}}. Visita [[Wikipedia:Proxies abiertos|la página informativa]] si estás afectado. <!-- Bloqueo hecho por bot -->" --really-run
