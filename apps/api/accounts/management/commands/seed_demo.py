"""Données de démonstration pour tester toute la plateforme.

    python manage.py seed_demo            # crée/complète les données démo
    python manage.py seed_demo --flush    # purge d'abord les données démo
    python manage.py seed_demo --streamers 8 --viewers 30

Idempotent : ré-exécutable sans doublon (clé = email @demo.neyla.tv / slug jeu).
Tout est synchrone et hors-ligne (Cloudflare/paiements en mode FAKE).
Identifiants de connexion : <email démo> / DemoPass2026!
"""

from __future__ import annotations

import json
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()

DOMAIN = "@demo.neyla.tv"
PASSWORD = "DemoPass2026!"

STAFF = [
    ("admin", "admin", "Admin Démo"),
    ("moderator", "moderator", "Modo Démo"),
    ("support", "support", "Support Démo"),
]
GAMES = [
    ("just-chatting", "Just Chatting"),
    ("valorant", "VALORANT"),
    ("league-of-legends", "League of Legends"),
    ("gta-v", "Grand Theft Auto V"),
    ("minecraft", "Minecraft"),
    ("fc-25", "EA Sports FC 25"),
]
BANNED = ["arnaque", "spam-link", "insulte1"]
FAKE_IMG = "https://fake.local/seed"


class Command(BaseCommand):
    help = "Génère des données de démonstration (utilisateurs, streams, paiements…)."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Purge les données démo avant.")
        parser.add_argument("--streamers", type=int, default=6)
        parser.add_argument("--viewers", type=int, default=20)

    def handle(self, *args, **opts):
        random.seed(42)
        if opts["flush"]:
            self._flush()
        staff = self._staff()
        admin = staff["admin"]
        self._fees()
        games = self._games()
        streamers = self._streamers(admin, games, opts["streamers"])
        viewers = self._viewers(streamers, opts["viewers"])
        self._subscriptions(streamers, viewers)
        self._invitations(streamers, viewers)
        self._support(staff.get("support"), viewers)
        self._achievements(streamers, viewers)
        self._banned_words(admin)
        self._reports(streamers)
        self.stdout.write(
            self.style.SUCCESS(
                f"Seed OK : {len(streamers)} streamers, {len(viewers)} viewers. "
                f"Connexion : <email>{DOMAIN} / {PASSWORD}"
            )
        )

    # --- helpers ---------------------------------------------------------

    def _mkuser(self, handle: str, display: str, role: str = "user"):
        email = f"{handle}{DOMAIN}"
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": handle, "display_name": display, "role": role},
        )
        if created:
            user.set_password(PASSWORD)
            user.bio = f"Compte démo : {display}."
            user.avatar_url = f"{FAKE_IMG}/avatar/{handle}.png"
            user.role = role
            user.save()
        return user

    def _flush(self):
        n, _ = User.objects.filter(email__endswith=DOMAIN).delete()
        self.stdout.write(f"[flush] {n} objets démo supprimés.")

    def _staff(self):
        staff = {}
        for handle, role, display in STAFF:
            u = self._mkuser(handle, display, role=role)
            if role == "admin":
                u.is_staff = True
                u.save(update_fields=["is_staff"])
            staff[role] = u
        return staff

    def _fees(self):
        from payments.models import FeeRule

        FeeRule.objects.get_or_create(
            product=FeeRule.Product.TIP,
            mode=FeeRule.Mode.PERCENTAGE,
            value=30,
            defaults={"is_active": True},
        )
        FeeRule.objects.get_or_create(
            product=FeeRule.Product.SUBSCRIPTION,
            mode=FeeRule.Mode.PERCENTAGE,
            value=30,
            defaults={"is_active": True},
        )

    def _games(self):
        from catalog.models import Game

        out = []
        for slug, name in GAMES:
            g, _ = Game.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "box_art_url": f"{FAKE_IMG}/game/{slug}.png"},
            )
            out.append(g)
        return out

    def _streamers(self, admin, games, count):
        from channels_app.models import Channel
        from streamers import services as streamer_services
        from streamers.services import AlreadyStreamerError
        from subscriptions import services as sub_services

        streamers = []
        for i in range(count):
            handle = f"streamer{i+1}"
            user = self._mkuser(handle, f"Streamer {i+1}")
            try:
                app = streamer_services.submit_application(user, "Seed démo.")
                streamer_services.approve_application(app, admin)
            except AlreadyStreamerError:
                pass
            channel = Channel.objects.get(user=user)
            channel.title = f"Live démo de {handle} 🎮"
            channel.category = random.choice(games)
            channel.thumbnail_url = f"{FAKE_IMG}/thumb/{handle}.png"
            channel.banner_url = f"{FAKE_IMG}/banner/{handle}.png"
            channel.social_links = {"twitter": f"https://x.com/{handle}"}
            channel.save()
            sub_services.set_tier(
                channel,
                price_aura=random.choice([50, 100, 200]),
                perks=["Badge abonné", "Stickers exclusifs"],
            )
            self._sessions(channel)
            streamers.append((user, channel))
        # ~moitié en direct
        for _user, channel in streamers[: max(1, count // 2)]:
            self._go_live(channel)
        return streamers

    def _sessions(self, channel):
        from channels_app.models import StreamSession

        if channel.sessions.exists():
            return
        now = timezone.now()
        for d in (5, 3, 1):
            start = now - timezone.timedelta(days=d, hours=2)
            StreamSession.objects.create(
                channel=channel,
                started_at=start,
                ended_at=start + timezone.timedelta(hours=random.randint(1, 4)),
                peak_viewers=random.randint(5, 500),
                title_snapshot=channel.title,
                category_snapshot=channel.category,
            )

    def _go_live(self, channel):
        from channels_app.models import StreamSession

        now = timezone.now()
        channel.is_live = True
        channel.last_live_started_at = now
        channel.save(update_fields=["is_live", "last_live_started_at", "updated_at"])
        if not channel.sessions.filter(ended_at__isnull=True).exists():
            StreamSession.objects.create(
                channel=channel,
                started_at=now - timezone.timedelta(minutes=20),
                peak_viewers=random.randint(10, 800),
                title_snapshot=channel.title,
                category_snapshot=channel.category,
            )
        self._chat(channel)

    def _chat(self, channel):
        try:
            import redis
            from django.conf import settings

            client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            key = f"chat:msgs:{channel.id}"
            if client.llen(key) > 0:
                return
            for n in range(5):
                client.rpush(
                    key,
                    json.dumps(
                        {
                            "id": f"seed-{channel.id}-{n}",
                            "user": {"username": "fan_demo", "display_name": "Fan", "role": "user"},
                            "content": random.choice(["GG !", "Salut 👋", "trop fort", "lets go"]),
                            "ts": int(timezone.now().timestamp() * 1000),
                        }
                    ),
                )
            client.ltrim(key, -100, -1)
        except Exception:  # noqa: BLE001 - best effort
            pass

    def _viewers(self, streamers, count):
        from payments import services as pay
        from payments.services import PaymentError
        from social.services import follow_user

        viewers = []
        if not streamers:
            return viewers
        for i in range(count):
            viewer = self._mkuser(f"viewer{i+1}", f"Viewer {i+1}")
            viewers.append(viewer)
            for _user, channel in random.sample(streamers, min(3, len(streamers))):
                try:
                    follow_user(viewer, channel.slug)
                except Exception:  # noqa: BLE001
                    pass
            if pay.get_wallet(viewer).aura_balance < 100:
                pay.create_purchase(viewer, 500)
            target = random.choice(streamers)[1]
            try:
                pay.send_tip(viewer, target.slug, random.choice([10, 20, 50]), "Bravo !")
            except PaymentError:
                pass
        # un payout depuis un streamer ayant reçu des tips
        try:
            _user, channel = streamers[0]
            if pay.get_wallet(channel.user).aura_balance >= 5:
                pay.request_payout(channel.user, 5)
        except Exception:  # noqa: BLE001
            pass
        return viewers

    def _subscriptions(self, streamers, viewers):
        from payments.services import PaymentError
        from subscriptions import services as sub_services
        from subscriptions.services import SubscriptionError

        if not streamers or not viewers:
            return
        for viewer in viewers[: max(1, len(viewers) // 2)]:
            _user, channel = random.choice(streamers)
            try:
                sub_services.subscribe(viewer, channel.slug)
            except (SubscriptionError, PaymentError):
                pass

    def _invitations(self, streamers, viewers):
        from invitations import services as invite_services

        if not streamers or len(viewers) < 2:
            return
        inviter = streamers[0][0]
        invite = invite_services.create_invite(inviter, max_uses=50)
        # Relie quelques viewers existants comme filleuls (sans recréer de compte).
        for viewer in viewers[:3]:
            if viewer.invited_by_id is None:
                viewer.invited_by = inviter
                viewer.save(update_fields=["invited_by"])
                invite.used_count += 1
        invite.save(update_fields=["used_count"])

    def _support(self, support_user, viewers):
        from notifications import services as notif_services

        if support_user is None or not viewers:
            return
        notif_services.send_support_message(
            viewers[0],
            "Bienvenue sur Neyla TV",
            "Merci d'avoir rejoint la plateforme. L'équipe support est là pour t'aider.",
            sender=support_user,
        )

    def _achievements(self, streamers, viewers):
        from gamification.services import check_and_award

        for _user, channel in streamers:
            check_and_award(channel.user, "first_login")
            check_and_award(channel.user, "first_stream")
        for viewer in viewers:
            check_and_award(viewer, "first_login")

    def _banned_words(self, admin):
        from moderation.models import BannedWord

        for w in BANNED:
            BannedWord.objects.get_or_create(word=w, defaults={"created_by": admin})

    def _reports(self, streamers):
        from moderation.services import create_report

        if len(streamers) < 2:
            return
        reporter = streamers[0][0]
        target = streamers[1][1]
        if not target.reports.exists():
            create_report(
                reporter,
                "spam",
                target_username=target.user.username,
                channel_slug=target.slug,
                details="Signalement de démonstration.",
            )
