"""Données de démonstration pour tester toute la plateforme.

    python manage.py seed_demo            # crée/complète les données démo
    python manage.py seed_demo --flush    # purge d'abord les données démo
    python manage.py seed_demo --streamers 8 --viewers 30

Idempotent : ré-exécutable sans doublon (clé = email @demo.neyla.tv / slug jeu).
Tout est synchrone et hors-ligne (Bunny Stream/paiements en mode FAKE).
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
# (slug, nom, macro-catégorie) — couvre les 5 groupes de « Parcourir ».
GAMES = [
    ("just-chatting", "Just Chatting", "chatting"),
    ("debats-actus", "Débats & Actus", "chatting"),
    ("valorant", "VALORANT", "games"),
    ("league-of-legends", "League of Legends", "games"),
    ("fc-25", "EA Sports FC 25", "games"),
    ("elden-ring", "Elden Ring", "games"),
    ("minecraft", "Minecraft", "games"),
    ("gta-v", "Grand Theft Auto V", "games"),
    ("counter-strike-2", "Counter-Strike 2", "games"),
    ("fortnite", "Fortnite", "games"),
    ("call-of-duty", "Call of Duty", "games"),
    ("dota-2", "Dota 2", "games"),
    ("street-fighter-6", "Street Fighter 6", "games"),
    ("apex-legends", "Apex Legends", "games"),
    ("voyages", "Voyages & Découvertes", "irl"),
    ("cuisine", "Cuisine africaine", "irl"),
    ("sport-fitness", "Sport & Fitness", "irl"),
    ("mode-beaute", "Mode & Beauté", "irl"),
    ("musique-live", "Musique live", "music"),
    ("dj-sets", "DJ Sets", "music"),
    ("afrobeats", "Afrobeats & Coupé-décalé", "music"),
    ("art-dessin", "Art & Dessin", "creative"),
    ("design-graphique", "Design graphique", "creative"),
    ("programmation", "Programmation", "creative"),
]
# Clips publics (CC0) servant de vidéos « Instant » de démonstration.
SHORT_CLIPS = [
    "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
    "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/friday.mp4",
]
SHORT_TITLES = [
    "Clutch 1v4 incroyable 🔥",
    "Recette du thiéboudienne en 60 s",
    "Le drop le plus fou de la soirée",
    "Speedpaint d'un masque Dan",
    "Ce but en FC 25… 😱",
    "Balade au marché Sandaga",
    "Freestyle afrobeats en live",
    "Astuce Minecraft que personne ne connaît",
    "Débat : le meilleur jollof ?",
    "Mon setup stream à petit budget",
]
SHORT_TITLES += [
    "Ace en ranked, la team en folie",
    "Attiéké poisson braisé : la vraie recette",
    "Coupé-décalé improvisé en plein live",
    "Portrait au stylo bille en 1 min",
    "Le penalty le plus froid du tournoi",
    "Tour de Saint-Louis en tuk-tuk",
    "Beat afro fait en direct",
    "Build Fortnite : la technique du 90",
    "Quel est le meilleur maquis d'Abidjan ?",
    "Unboxing de ma nouvelle webcam (merci le chat !)",
    "Mon premier clutch sur CS2",
    "Workout de 60 s sans matériel",
    "Tenue wax du jour ✨",
    "Live coding : un bot pour mon chat",
    "Le chat choisit ma musique 🎶",
]
# Personae des streamers démo : (nom affiché, bio, tags, pseudo réseaux).
PERSONAS = [
    (
        "Awa Gaming",
        "Valorant et bonne humeur depuis Dakar 🇸🇳. Live tous les soirs à 20 h.",
        ["Français", "Wolof", "FPS"],
        "awa.gaming",
    ),
    (
        "Kofi Plays",
        "Joueur LoL main support. On grimpe ensemble, sans rage 😄",
        ["Français", "Compétitif"],
        "kofiplays",
    ),
    (
        "Mariam Cuisine",
        "Recettes d'Afrique de l'Ouest en direct, du marché à l'assiette.",
        ["Français", "Bambara", "Cuisine"],
        "mariam.cuisine",
    ),
    (
        "DJ Sahel",
        "Afrobeats, coupé-décalé et amapiano. Sets live le week-end 🎧",
        ["Français", "Musique"],
        "djsahel",
    ),
    (
        "Ibou Talks",
        "Débats, actus et grosses discussions avec le chat.",
        ["Français", "Wolof", "Discussion"],
        "ibou.talks",
    ),
    (
        "Fatou Art",
        "Illustratrice. Speedpaint, portraits et commandes en live.",
        ["Français", "Art"],
        "fatou.art",
    ),
    (
        "Yao FC",
        "FC 25, Ultimate Team et tournois communautaires ⚽",
        ["Français", "Sport"],
        "yao.fc",
    ),
    (
        "Nana Voyage",
        "Je vous emmène partout : marchés, plages, villages 🌍",
        ["Français", "IRL", "Voyage"],
        "nana.voyage",
    ),
    (
        "Moussa Dev",
        "Développeur. Je code des outils pour streamers en direct.",
        ["Français", "Tech"],
        "moussa.dev",
    ),
    (
        "Aïcha Style",
        "Mode wax, beauté et conseils petit budget.",
        ["Français", "Mode"],
        "aicha.style",
    ),
    (
        "Sékou Craft",
        "Minecraft survie et builds géants avec la commu.",
        ["Français", "Bambara", "Chill"],
        "sekou.craft",
    ),
    (
        "Binta Fit",
        "Coach sportive. Séances live gratuites, tous niveaux 💪",
        ["Français", "Sport"],
        "binta.fit",
    ),
    (
        "Koffi Sound",
        "Guitare, voix et reprises à la demande du chat.",
        ["Français", "Musique"],
        "koffi.sound",
    ),
    (
        "Adama Ranked",
        "CS2 et Apex. Grind, stratégie et bonne ambiance.",
        ["Français", "FPS"],
        "adama.ranked",
    ),
    (
        "Rokia Design",
        "Design graphique : logos et overlays offerts aux petits streamers.",
        ["Français", "Créatif"],
        "rokia.design",
    ),
    (
        "Tidiane GTA",
        "RP GTA V sur serveur francophone, histoires folles garanties.",
        ["Français", "RP"],
        "tidiane.gta",
    ),
    (
        "Salif Fighter",
        "Street Fighter 6, sets FT5 contre le chat 🥊",
        ["Français", "Combat"],
        "salif.fighter",
    ),
    (
        "Kadi Chill",
        "Just Chatting, jeux indés et papotage du dimanche.",
        ["Français", "Nouchi", "Chill"],
        "kadi.chill",
    ),
    (
        "Oumar Dota",
        "Dota 2 depuis 10 ans. Coaching gratuit le mercredi.",
        ["Français", "MOBA"],
        "oumar.dota",
    ),
    (
        "Grâce Live",
        "Afrobeats, danse et défis avec la communauté ✨",
        ["Français", "Musique", "Danse"],
        "grace.live",
    ),
]
# Messages de chat démo (français, wolof, nouchi, emojis).
CHAT_LINES = [
    "Salut tout le monde 👋",
    "GG !!! 🔥🔥",
    "Nanga def ? 😄",
    "On est ensemble 💪",
    "C'est validé ça",
    "Trop fort le clutch",
    "Le son est nickel ce soir",
    "Djamm rek 🙏",
    "Y'a pas drap, ça gâte !",
    "Première fois ici, la vibe est top",
    "Abonné depuis 3 mois, toujours au top ❤️",
    "Quelqu'un est de Bamako ici ?",
    "Abidjan dans la place 🇨🇮",
    "Dakar représente 🇸🇳",
    "Tu joues quoi après ?",
    "LOL 😂😂",
    "Mashallah, magnifique",
    "On veut un deuxième round !",
    "Le boss final arrive…",
    "Wesh la team 👊",
    "Merci pour le live 🙌",
    "Ça c'est du niveau pro",
    "Ma connexion lag un peu, c'est moi ?",
    "Le chat est chaud ce soir 😅",
    "Bravo pour les 1000 followers !",
    "Tip envoyé, continue comme ça ✨",
    "C'est gâté gâté 🔥",
    "Je reste jusqu'à la fin",
    "Quel setup tu utilises ?",
    "Jërëjëf pour le stream",
]
CHAT_USERS = [
    ("fatou_sn", "Fatou_SN"),
    ("blaz_abj", "BlazAbj"),
    ("moussa221", "Moussa221"),
    ("aminata.k", "Aminata.K"),
    ("le_vrai_yao", "LeVraiYao"),
    ("kiki_bko", "KikiBko"),
    ("drogba_fan", "DrogbaFan"),
    ("ndeye", "Ndeye"),
    ("papis_tv", "PapisTV"),
    ("zoum_zoum", "ZoumZoum"),
    ("seydou_gaming", "SeydouGaming"),
    ("awa_lover", "AwaLover"),
]
TIP_MESSAGES = [
    "Bravo !",
    "Pour la nouvelle webcam 📷",
    "Continue comme ça 🔥",
    "Joyeux anniversaire !",
    "Le meilleur stream du soir",
    "Pour le thé ☕",
    "Jërëjëf pour les conseils",
    "On est ensemble 💪",
]
# Soldes cibles pour afficher chaque palier Aura (1 · 100 · 1 000 · 5 000 · 10 000).
TIER_BALANCES = [42, 180, 1_450, 6_200, 12_500]
BANNED = ["arnaque", "spam-link", "insulte1"]
CHARITIES = [
    (
        "education-numerique",
        "Éducation Numérique Afrique",
        "SN",
        "Soutien à l'accès au numérique dans les écoles ouest-africaines.",
    ),
    (
        "sante-mentale-jeunes",
        "Santé Mentale des Jeunes",
        "CI",
        "Programmes d'écoute et de prévention pour la jeunesse.",
    ),
    (
        "environnement-sahel",
        "Environnement Sahel",
        "BF",
        "Reforestation et lutte contre la désertification.",
    ),
]
# Titre de live selon la macro-catégorie.
TITLES = {
    "games": "{name} — run du soir 🎮",
    "chatting": "{name} : on refait le monde 💬",
    "irl": "{name} en direct de Dakar 🌍",
    "music": "{name} — session live 🎧",
    "creative": "{name} : on crée ensemble 🎨",
}
# Images de démo : service de placeholder déterministe (rendu réaliste).
IMG = "https://picsum.photos/seed"


class Command(BaseCommand):
    help = "Génère des données de démonstration (utilisateurs, streams, paiements…)."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Purge les données démo avant.")
        parser.add_argument("--streamers", type=int, default=20)
        parser.add_argument("--viewers", type=int, default=40)
        parser.add_argument(
            "--live-ratio",
            type=float,
            default=1.0,
            help="Proportion de streamers en direct (0..1). 1.0 = tous en live.",
        )

    def handle(self, *args, **opts):
        random.seed(42)
        if opts["flush"]:
            self._flush()
        staff = self._staff()
        admin = staff["admin"]
        self._fees()
        games = self._games()
        streamers = self._streamers(admin, games, opts["streamers"], opts["live_ratio"])
        viewers = self._viewers(streamers, opts["viewers"])
        self._subscriptions(streamers, viewers)
        self._invitations(streamers, viewers)
        self._support(staff.get("support"), viewers)
        self._achievements(streamers, viewers)
        self._banned_words(admin)
        self._reports(streamers)
        self._charity(streamers, viewers)
        self._shorts(streamers, viewers)
        self._monetization_scenarios(streamers, viewers)
        self._announcements_events()
        self._goal_activity(streamers, viewers)
        self._tier_balances(streamers, viewers)
        self.stdout.write(
            self.style.SUCCESS(
                f"Seed OK : {len(streamers)} streamers, {len(viewers)} viewers. "
                f"Connexion : <email>{DOMAIN} / {PASSWORD}"
            )
        )

    # --- helpers ---------------------------------------------------------

    def _free_username(self, preferred: str) -> str:
        """Renvoie un username libre comme username ET comme slug de chaîne.

        Évite toute collision avec des comptes/chaînes réels déjà présents
        (ex. une chaîne `admin` existante) : on ne touche jamais aux vraies
        données, on choisit simplement un identifiant disponible.
        """
        from channels_app.models import Channel

        base = preferred
        candidate = base
        i = 1
        while (
            User.objects.filter(username=candidate).exists()
            or Channel.objects.filter(slug=candidate).exists()
        ):
            i += 1
            candidate = f"{base}{i}"
        return candidate

    def _mkuser(self, handle: str, display: str, role: str = "user"):
        email = f"{handle}{DOMAIN}"
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            # username/slug libre → le signal d'auto-création de Channel ne
            # heurtera pas une chaîne réelle existante.
            username = self._free_username(handle)
            user = User.objects.create(
                email=email, username=username, display_name=display, role=role
            )
        # Garantit toujours un login fonctionnel, même en ré-exécution.
        user.set_password(PASSWORD)
        user.is_active = True
        user.role = role
        if not user.bio:
            user.bio = f"Compte démo : {display}."
        if not user.avatar_url:
            user.avatar_url = f"{IMG}/{handle}-av/200/200"
        user.save()
        return user

    def _flush(self):
        """Purge TOUTES les données démo (pas seulement les comptes)."""
        from announcements.models import SiteAnnouncement
        from catalog.models import Game
        from charity.models import Charity, CharityDisbursement, CharityEvent, PlatformEvent

        n, _ = User.objects.filter(email__endswith=DOMAIN).delete()
        demo_events = CharityEvent.objects.filter(slug__startswith="charity-day-")
        CharityDisbursement.objects.filter(event__in=demo_events).delete()
        for event in demo_events:
            event.donations.all().delete()
        demo_events.delete()  # le signal supprime aussi les PlatformEvent miroirs
        PlatformEvent.objects.filter(slug__startswith="demo-").delete()
        SiteAnnouncement.objects.filter(title__startswith="[Démo]").delete()
        Charity.objects.filter(slug__in=[c[0] for c in CHARITIES], donations__isnull=True).delete()
        # Catégories démo non utilisées par une chaîne réelle.
        Game.objects.filter(slug__in=[g[0] for g in GAMES], channels__isnull=True).delete()
        self.stdout.write(f"[flush] {n} objets démo supprimés (comptes, événements, catégories).")

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
        """Règles par défaut, seulement si le produit n'en a aucune active
        (n'écrase jamais un taux modifié par l'admin, pas de doublon)."""
        from payments.models import FeeRule

        for product, value in (
            (FeeRule.Product.TIP, 30),
            (FeeRule.Product.SUBSCRIPTION, 30),
            (FeeRule.Product.PURCHASE, 1),
        ):
            if not FeeRule.objects.filter(product=product, is_active=True).exists():
                FeeRule.objects.create(
                    product=product, mode=FeeRule.Mode.PERCENTAGE, value=value, is_active=True
                )

    def _games(self):
        from catalog.models import Game

        out = []
        for slug, name, group in GAMES:
            g, _ = Game.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "group": group,
                    "box_art_url": f"{IMG}/{slug}-box/320/440",
                },
            )
            if g.group != group:
                g.group = group
                g.save(update_fields=["group"])
            out.append(g)
        return out

    def _streamers(self, admin, games, count, live_ratio=1.0):
        from channels_app.models import Channel
        from streamers import services as streamer_services
        from streamers.services import AlreadyStreamerError
        from subscriptions import services as sub_services

        # Tourniquet par macro-catégorie : chaque groupe a des chaînes en direct.
        by_group: dict[str, list] = {}
        for g in games:
            by_group.setdefault(g.group, []).append(g)
        rotation = []
        while any(by_group.values()):
            for group in list(by_group):
                if by_group[group]:
                    rotation.append(by_group[group].pop(0))

        streamers = []
        for i in range(count):
            handle = f"streamer{i+1}"
            user = self._mkuser(handle, f"Streamer {i+1}")
            try:
                app = streamer_services.submit_application(user, "Seed démo.")
                streamer_services.approve_application(app, admin)
            except AlreadyStreamerError:
                pass
            # Répartit les streamers sur toutes les catégories (couverture large).
            game = rotation[i % len(rotation)]
            channel = Channel.objects.get(user=user)
            # Anciennes URLs factices (avant Bunny) : flux HLS de démo lisible.
            if "fake.local" in channel.playback_url:
                from channels_app.bunny import FAKE_HLS_URL

                channel.playback_url = FAKE_HLS_URL
            channel.title = TITLES.get(game.group, "{name} — live 🎮").format(name=game.name)
            channel.category = game
            channel.thumbnail_url = f"{IMG}/{handle}-th/640/360"
            channel.banner_url = f"{IMG}/{handle}-bn/1200/300"
            persona = PERSONAS[i % len(PERSONAS)]
            display, bio, tags, social = persona
            if i >= len(PERSONAS):
                display, social = f"{display} {i // len(PERSONAS) + 1}", f"{social}{i + 1}"
            user.display_name = display
            if not user.bio or user.bio.startswith("Compte démo"):
                user.bio = bio
            user.save(update_fields=["display_name", "bio"])
            channel.tags = tags
            channel.social_links = {
                "instagram": f"https://instagram.com/{social}",
                "twitter": f"https://x.com/{social.replace('.', '_')}",
                "youtube": f"https://youtube.com/@{social.replace('.', '')}",
                "tiktok": f"https://tiktok.com/@{social}",
            }
            # Un tiers des chaînes affichent un objectif (abonnés ou Aura reçue).
            if i % 3 == 0:
                channel.goal_kind = "subs" if i % 2 == 0 else "tips"
                channel.goal_title = (
                    "Objectif : nouveaux abonnés"
                    if channel.goal_kind == "subs"
                    else "Objectif : nouvelle webcam"
                )
                channel.goal_target = 10 if channel.goal_kind == "subs" else 5000
                channel.goal_started_at = timezone.now() - timezone.timedelta(days=7)
            channel.save()
            sub_services.set_tier(
                channel,
                price_aura=random.choice([50, 100, 200]),
                perks=["Badge abonné", "Stickers exclusifs"],
            )
            self._sessions(channel)
            streamers.append((user, channel))
        # En direct pour remplir l'accueil et « Parcourir » (tous par défaut).
        ratio = max(0.0, min(1.0, live_ratio))
        live_count = max(1, round(len(streamers) * ratio)) if streamers else 0
        for _user, channel in streamers[:live_count]:
            self._go_live(channel)
        self.stdout.write(f"[live] {live_count}/{len(streamers)} streamers en direct.")
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
        self._set_viewers(channel.id, random.randint(5, 5000))
        self._chat(channel)

    def _set_viewers(self, channel_id, count):
        """Pose un compteur de viewers en Redis (rendu réaliste cartes/sidebar)."""
        try:
            import redis
            from django.conf import settings

            client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            client.set(f"chat:viewers:{channel_id}", count, ex=60 * 60)
        except Exception:  # noqa: BLE001 - best effort
            pass

    def _chat(self, channel):
        """25 à 40 messages variés (pseudos, rôles, abonnés) par chaîne en direct."""
        try:
            import redis
            from django.conf import settings

            client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            key = f"chat:msgs:{channel.id}"
            if client.llen(key) >= 25:
                return
            client.delete(key)
            now_ms = int(timezone.now().timestamp() * 1000)
            count = random.randint(25, 40)
            for n in range(count):
                username, display = random.choice(CHAT_USERS)
                role = "moderator" if username == "papis_tv" else "user"
                client.rpush(
                    key,
                    json.dumps(
                        {
                            "id": f"seed-{channel.id}-{n}",
                            "user": {
                                "username": username,
                                "display_name": display,
                                "role": role,
                                "is_subscriber": sum(map(ord, username)) % 3 == 0 or role != "user",
                            },
                            "content": random.choice(CHAT_LINES),
                            "ts": now_ms - (count - n) * random.randint(4_000, 20_000),
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
            # Chacun suit 3 à 8 chaînes ; les 3 « stars » sont suivies par presque tous.
            picks = random.sample(streamers, min(random.randint(3, 8), len(streamers)))
            stars = [s for s in streamers[:3] if random.random() < 0.85]
            for _user, channel in {c.pk: (u, c) for u, c in picks + stars}.values():
                try:
                    follow_user(viewer, channel.slug)
                except Exception:  # noqa: BLE001
                    pass
            # Les 10 premiers ont de quoi donner au Charity Day et offrir des abos.
            target_balance = 2500 if i < 10 else 500
            balance = pay.get_wallet(viewer).aura_balance
            if balance < target_balance:
                pay.create_purchase(viewer, target_balance - balance)
            target = random.choice(streamers)[1]
            try:
                pay.send_tip(
                    viewer, target.slug, random.choice([10, 20, 50]), random.choice(TIP_MESSAGES)
                )
            except PaymentError:
                pass
        # un retrait (Wave) depuis un streamer ayant reçu des tips
        try:
            _user, channel = streamers[0]
            amount = pay.withdrawable_balance(channel.user)
            if amount >= pay.withdrawal_min_aura():
                pay.create_payout(
                    channel.user,
                    amount,
                    destination_provider="wave",
                    destination_phone="+221770000001",
                )
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

    def _charity(self, streamers, viewers):
        """Sème 3 associations + 2 Charity Days (1 en cours, 1 à venir) + dons demo."""
        from django.utils import timezone

        from charity import services as charity_services
        from charity.models import Charity, CharityEvent

        charities = []
        for slug, name, country, desc in CHARITIES:
            c, _ = Charity.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "country": country,
                    "description": desc,
                    "logo_url": f"{IMG}/{slug}/120/120",
                },
            )
            charities.append(c)

        now = timezone.now()
        # Événement EN COURS (commencé hier, finit dans 6 jours).
        current, _ = CharityEvent.objects.get_or_create(
            slug=f"charity-day-{now:%Y-%m}",
            defaults={
                "title": f"Charity Day {now:%B %Y}",
                "theme": "Éducation & Inclusion",
                "description_md": (
                    "**1 jour par mois, on stream pour une cause.**\n\n"
                    "Choisis ton association, fais ton don en Aura. "
                    "Les montants reversés sont publiés ci-dessous, reçu à l'appui."
                ),
                "starts_at": now - timezone.timedelta(days=1),
                "ends_at": now + timezone.timedelta(days=6),
                "floor_aura": 10,
                "cover_url": f"{IMG}/charity-current/1200/300",
                "is_published": True,
            },
        )
        current.beneficiaries.set(charities)

        # Événement à venir (mois prochain).
        future_when = now + timezone.timedelta(days=30)
        future, _ = CharityEvent.objects.get_or_create(
            slug=f"charity-day-{future_when:%Y-%m}",
            defaults={
                "title": f"Charity Day {future_when:%B %Y}",
                "theme": "Santé & Bien-être",
                "starts_at": future_when,
                "ends_at": future_when + timezone.timedelta(days=7),
                "floor_aura": 20,
                "cover_url": f"{IMG}/charity-future/1200/300",
                "is_published": True,
            },
        )
        future.beneficiaries.set(charities[:2])

        # Quelques dons demo (mix viewers + streamers, montants variés).
        if not viewers:
            return
        import contextlib

        donors = viewers[:8] + [u for u, _ch in streamers[:2]]
        amounts = [50, 25, 200, 75, 500, 30, 1200, 80, 300, 90]
        for donor, amount in zip(donors, amounts, strict=False):
            cause = random.choice(charities)
            with contextlib.suppress(Exception):
                charity_services.donate(
                    donor,
                    current.slug,
                    cause.slug,
                    amount,
                    message="bravo !",
                    is_anonymous=(amount > 1000),
                )

    def _shorts(self, streamers, viewers):
        """~50 vidéos « Instant » prêtes, avec vues et likes réalistes."""
        from shorts.models import Short, ShortLike

        if not streamers:
            return
        now = timezone.now()
        created = 0
        for i in range(50):
            user, channel = streamers[i % len(streamers)]
            guid = f"demo-short-{channel.slug}-{i}"
            short, was_created = Short.objects.get_or_create(
                video_guid=guid,
                defaults={
                    "channel": channel,
                    "title": SHORT_TITLES[i % len(SHORT_TITLES)],
                    "status": Short.Status.READY,
                    "playback_url": SHORT_CLIPS[i % len(SHORT_CLIPS)],
                    "thumbnail_url": f"{IMG}/short-{i}/360/640",
                    "duration_s": random.randint(8, 58),
                    "view_count": random.randint(50, 25_000),
                    "published_at": now - timezone.timedelta(hours=random.randint(1, 240)),
                },
            )
            if was_created:
                created += 1
                for fan in random.sample(viewers, min(len(viewers), random.randint(0, 12))):
                    ShortLike.objects.get_or_create(user=fan, short=short)
                short.like_count = short.likes.count() + random.randint(0, 400)
                short.save(update_fields=["like_count"])
        self.stdout.write(f"[instant] {created} vidéos courtes créées.")

    def _goal_activity(self, streamers, viewers):
        """Remplit les objectifs de chaîne à 30-80 % (abonnements ou tips réels)."""
        from channels_app.views import goal_progress
        from payments import services as pay
        from subscriptions import services as sub_services

        fans = viewers[10 : -len(TIER_BALANCES)] or viewers
        for _user, channel in streamers:
            if channel.goal_target <= 0:
                continue
            wanted = int(channel.goal_target * random.uniform(0.3, 0.8))
            for fan in random.sample(fans, len(fans)):
                if goal_progress(channel) >= wanted:
                    break
                try:
                    if channel.goal_kind == "subs":
                        sub_services.subscribe(fan, channel.slug)
                    else:
                        amount = random.choice([100, 200, 300])
                        pay.create_purchase(fan, amount)
                        pay.send_tip(fan, channel.slug, amount, random.choice(TIP_MESSAGES))
                except Exception:  # noqa: BLE001, S112 - déjà abonné, solde insuffisant…
                    continue

    def _tier_balances(self, streamers, viewers):
        """Les 5 derniers spectateurs atteignent chacun un palier Aura différent.

        Achat si le solde est trop bas, gros tip à une chaîne s'il est trop haut :
        tout passe par le grand livre (reconcile_wallets reste à zéro écart).
        """
        from payments import services as pay

        if len(viewers) < len(TIER_BALANCES) or not streamers:
            return
        for viewer, target in zip(viewers[-len(TIER_BALANCES) :], TIER_BALANCES, strict=True):
            balance = pay.get_wallet(viewer).aura_balance
            diff = target - balance
            try:
                if diff > 0:
                    pay.create_purchase(viewer, diff)
                elif -diff >= pay.tip_min_aura():
                    channel = random.choice(streamers)[1]
                    pay.send_tip(viewer, channel.slug, -diff, random.choice(TIP_MESSAGES))
            except Exception:  # noqa: BLE001 - best effort
                pass
        self.stdout.write(f"[aura] paliers démo : {', '.join(map(str, TIER_BALANCES))} Aura.")

    def _monetization_scenarios(self, streamers, viewers):
        """Cas réalistes : abonnements offerts, renouvellement, achat en attente,
        retrait Wave en cours, versement Charity Day."""
        import contextlib

        from charity.models import CharityDisbursement, CharityEvent
        from payments import services as pay
        from payments.models import Payout, Purchase
        from subscriptions import services as sub_services
        from subscriptions.models import Subscription

        if len(streamers) < 2 or len(viewers) < 4:
            return
        # Abonnements offerts (sans renouvellement automatique).
        for gifter, recipient in ((viewers[0], viewers[1]), (viewers[2], viewers[3])):
            with contextlib.suppress(Exception):
                sub_services.gift_subscription(gifter, streamers[1][1].slug, recipient.username)

        # Un renouvellement mensuel au prix verrouillé.
        due = (
            Subscription.objects.filter(status=Subscription.Status.ACTIVE, auto_renew=True)
            .exclude(subscriber__in=[viewers[1], viewers[3]])
            .first()
        )
        if due is not None:
            Subscription.objects.filter(pk=due.pk).update(current_period_end=timezone.now())
            sub_services.process_due_subscriptions()

        # Achat carte en attente de confirmation (retour Stripe non reçu).
        if not Purchase.objects.filter(user=viewers[4 % len(viewers)], status="pending").exists():
            Purchase.objects.create(
                user=viewers[4 % len(viewers)],
                credits=1000,
                fiat_amount=pay._fiat_for(1000),
                provider="stripe",
                provider_ref="cs_demo_pending",
            )

        # Un mécène tippe généreusement streamer1, qui retire sur Wave
        # (retrait « en cours de versement ») ; streamer3 achète de l'Aura (1 %).
        admin = User.objects.filter(email=f"admin{DOMAIN}").first()
        star, star_channel = streamers[0]
        if not Payout.objects.filter(user=star).exists():
            patron = viewers[5 % len(viewers)]
            with contextlib.suppress(Exception):
                pay.create_purchase(patron, 2500)
                pay.send_tip(patron, star_channel.slug, 2000, "Pour la nouvelle webcam !")
            amount = pay.withdrawable_balance(star)
            if amount >= pay.withdrawal_min_aura():
                with contextlib.suppress(Exception):
                    payout = pay.create_payout(
                        star,
                        amount,
                        destination_provider="wave",
                        destination_phone="+221771234567",
                    )
                    if admin is not None:
                        pay.resolve_payout(admin, payout, "processing")
            with contextlib.suppress(Exception):
                pay.create_purchase(streamers[2][0], 1000)

        # Premier versement à une association (transparence Charity Day).
        event = (
            CharityEvent.objects.filter(slug__startswith="charity-day-")
            .order_by("starts_at")
            .first()
        )
        if event is not None and not event.disbursements.exists():
            charity = event.beneficiaries.first()
            if charity is not None and event.total_aura_cached:
                aura = event.total_aura_cached // 2
                CharityDisbursement.objects.create(
                    event=event,
                    charity=charity,
                    aura_amount=aura,
                    fiat_amount_xof=int(pay._fiat_for(aura)),
                    reference="VIR-DEMO-0001",
                    paid_at=timezone.localdate(),
                )

    def _announcements_events(self):
        from announcements.models import SiteAnnouncement
        from charity.models import PlatformEvent

        now = timezone.now()
        SiteAnnouncement.objects.get_or_create(
            title="[Démo] Bienvenue sur Neyla TV",
            defaults={
                "body": "Découvre les vidéos Instant et soutiens tes streamers en Aura !",
                "level": SiteAnnouncement.Level.INFO,
                "display_mode": SiteAnnouncement.DisplayMode.TICKER,
                "ends_at": now + timezone.timedelta(days=30),
                "cta_label": "Voir Instant",
                "cta_url": "https://neyla.tv/instant",
            },
        )
        for slug, title, kind, delta_days in (
            ("demo-tournoi-fc25", "Tournoi FC 25 — Coupe de Dakar", "tournament", 3),
            ("demo-premiere-docu", "Première : « Créateurs du Sahel »", "premiere", 7),
        ):
            PlatformEvent.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "kind": kind,
                    "description_md": "Événement de démonstration.",
                    "cover_url": f"{IMG}/{slug}/1200/300",
                    "link_url": "https://neyla.tv/calendrier",
                    "starts_at": now + timezone.timedelta(days=delta_days),
                    "ends_at": now + timezone.timedelta(days=delta_days, hours=3),
                    "is_published": True,
                    "featured": True,
                },
            )
