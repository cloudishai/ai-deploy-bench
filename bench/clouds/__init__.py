"""Cloud adapters keyed by cloud id; GitHub covers scratch repositories and images."""

from bench.clouds.base import Cloud
from bench.clouds.cloudish import Cloudish
from bench.clouds.digitalocean import DigitalOcean
from bench.clouds.github import GitHub
from bench.clouds.render import Render
from bench.clouds.vercel import Vercel

ADAPTERS: dict[str, type[Cloud]] = {c.id: c for c in (Cloudish, DigitalOcean, Render, Vercel)}
