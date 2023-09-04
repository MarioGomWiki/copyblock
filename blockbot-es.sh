#!/usr/bin/env bash

# P2P proxies (bot blocks)

python copyblock.py --source-user ST47ProxyBot --comment-pattern '(?i)^{{blocked p2p proxy' --block-reason '{{Proxy P2P bloqueado}}. Visita [[Wikipedia:Proxies abiertos|la página informativa]] si estás afectado. <!-- Proxy P2P confirmado por API -->' --really-run

# Regular proxies

python copyyblock.py --comment-pattern '(?i)^{{blocked ?proxy' --block-reason '{{proxy bloqueado}}. Visita [[Wikipedia:Proxies abiertos|la página informativa]] si estás afectado. <!-- Bloqueo hecho por bot -->' --really-run
python copyblock.py --comment-pattern '(?i)^{{blocked ?proxy' --ranges --block-reason '{{proxy bloqueado}}. Visita [[Wikipedia:Proxies abiertos|la página informativa]] si estás afectado. <!-- Bloqueo hecho por bot -->' --really-run

# Webhosts

python copyblock.py --comment-pattern '(?i)^{{(?:colocation)?webhost' --ranges --block-reason '{{Webhost bloqueado}}. Visita [[Wikipedia:Proxies abiertos|la página informativa]] si estás afectado. <!-- Bloqueo hecho por bot -->' --really-run
