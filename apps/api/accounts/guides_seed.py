"""Contenu de référence des guides/tutoriels (FR/EN/PT).

Sert à peupler la base (migration de données + commande de seed). Les `slug`
et `step_id` sont STABLES : ils servent de clé de progression
(`GuideProgress.key = "<slug>:<step_id>"`). Ne pas les renommer.

Fichier de données : lignes longues (prose localisée) volontaires.
"""

# ruff: noqa: E501

from __future__ import annotations

GUIDES_SEED = [
    {
        "slug": "getting-started",
        "icon": "rocket",
        "order": 1,
        "title": {
            "fr": "Premiers pas",
            "en": "Getting started",
            "pt": "Primeiros passos",
        },
        "desc": {
            "fr": "Crée ton compte et configure ton profil pour bien démarrer.",
            "en": "Create your account and set up your profile to get started.",
            "pt": "Cria a tua conta e configura o teu perfil para começar bem.",
        },
        "steps": [
            {
                "step_id": "verify-email",
                "title": {
                    "fr": "Vérifie ton adresse email",
                    "en": "Verify your email",
                    "pt": "Verifica o teu email",
                },
                "body": {
                    "fr": "Confirme ton email via le lien reçu pour débloquer toutes les fonctionnalités (chat, achats, notifications).",
                    "en": "Confirm your email via the link you received to unlock all features (chat, purchases, notifications).",
                    "pt": "Confirma o email pelo link recebido para desbloquear todas as funcionalidades (chat, compras, notificações).",
                },
            },
            {
                "step_id": "profile",
                "title": {
                    "fr": "Personnalise ton profil",
                    "en": "Customize your profile",
                    "pt": "Personaliza o teu perfil",
                },
                "body": {
                    "fr": "Dans Paramètres, ajoute un nom d'affichage, un avatar, une bannière, une bio, ton pays et tes réseaux sociaux.",
                    "en": "In Settings, add a display name, avatar, banner, bio, country and social links.",
                    "pt": "Em Definições, adiciona nome, avatar, banner, bio, país e redes sociais.",
                },
            },
            {
                "step_id": "follow",
                "title": {
                    "fr": "Suis tes premières chaînes",
                    "en": "Follow your first channels",
                    "pt": "Segue os teus primeiros canais",
                },
                "body": {
                    "fr": "Parcours les lives et catégories, puis suis des créateurs : ils apparaîtront dans ta barre latérale et l'onglet Suivis.",
                    "en": "Browse lives and categories, then follow creators: they appear in your sidebar and the Following tab.",
                    "pt": "Explora lives e categorias e segue criadores: aparecem na barra lateral e no separador Seguindo.",
                },
            },
        ],
    },
    {
        "slug": "streaming-setup",
        "icon": "broadcast",
        "order": 2,
        "title": {
            "fr": "Configurer et démarrer le streaming",
            "en": "Set up and start streaming",
            "pt": "Configurar e começar a transmitir",
        },
        "desc": {
            "fr": "De la demande streamer à ton premier direct avec OBS.",
            "en": "From streamer application to your first live with OBS.",
            "pt": "Do pedido de streamer ao teu primeiro direto com OBS.",
        },
        "steps": [
            {
                "step_id": "apply",
                "title": {
                    "fr": "Deviens streamer",
                    "en": "Become a streamer",
                    "pt": "Torna-te streamer",
                },
                "body": {
                    "fr": "Depuis le Dashboard, fais une demande d'accès streamer. Une fois approuvée, ta clé RTMPS et les outils de diffusion se débloquent.",
                    "en": "From the Dashboard, request streamer access. Once approved, your RTMPS key and broadcast tools unlock.",
                    "pt": "No Painel, pede acesso de streamer. Após aprovação, a tua chave RTMPS e ferramentas são desbloqueadas.",
                },
            },
            {
                "step_id": "obs",
                "title": {"fr": "Configure OBS", "en": "Configure OBS", "pt": "Configura o OBS"},
                "body": {
                    "fr": "Dans l'onglet Diffusion, copie le serveur RTMPS et ta clé de stream. Dans OBS : Paramètres → Flux → Service « Personnalisé », colle serveur et clé.",
                    "en": "In the Broadcast tab, copy the RTMPS server and your stream key. In OBS: Settings → Stream → Custom service, paste server and key.",
                    "pt": "No separador Transmissão, copia o servidor RTMPS e a chave. No OBS: Definições → Transmissão → serviço Personalizado, cola servidor e chave.",
                },
            },
            {
                "step_id": "infos",
                "title": {
                    "fr": "Renseigne les infos du stream",
                    "en": "Fill in stream info",
                    "pt": "Preenche as informações",
                },
                "body": {
                    "fr": "Onglet Aperçu : définis un titre, une catégorie et des tags pour rendre ton live découvrable.",
                    "en": "Overview tab: set a title, category and tags to make your stream discoverable.",
                    "pt": "Separador Visão geral: define título, categoria e tags para o teu stream ser descoberto.",
                },
            },
            {
                "step_id": "golive",
                "title": {"fr": "Passe en direct", "en": "Go live", "pt": "Fica ao vivo"},
                "body": {
                    "fr": "Lance « Démarrer le streaming » dans OBS (ou le bouton Passer en direct pour une démo). Ton minuteur de session et tes spectateurs s'affichent en haut du studio.",
                    "en": "Start streaming in OBS (or the Go live button for a demo). Your session timer and viewers show at the top of the studio.",
                    "pt": "Inicia a transmissão no OBS (ou o botão Ficar ao vivo para demo). O cronómetro e os espectadores aparecem no topo do estúdio.",
                },
            },
            {
                "step_id": "overlay",
                "title": {
                    "fr": "Ajoute l'overlay d'alertes",
                    "en": "Add the alerts overlay",
                    "pt": "Adiciona o overlay de alertas",
                },
                "body": {
                    "fr": "Onglet Diffusion : copie l'URL de l'overlay et ajoute-la comme source navigateur dans OBS pour afficher followers, abos et tips en direct.",
                    "en": "Broadcast tab: copy the overlay URL and add it as a browser source in OBS to show followers, subs and tips live.",
                    "pt": "Separador Transmissão: copia o URL do overlay e adiciona-o como fonte de navegador no OBS para mostrar seguidores, assinantes e tips ao vivo.",
                },
            },
        ],
    },
    {
        "slug": "monetization",
        "icon": "coins",
        "order": 3,
        "title": {"fr": "Monétisation", "en": "Monetization", "pt": "Monetização"},
        "desc": {
            "fr": "Aura, abonnements, tips et retraits.",
            "en": "Aura, subscriptions, tips and payouts.",
            "pt": "Aura, assinaturas, tips e levantamentos.",
        },
        "steps": [
            {
                "step_id": "buy-aura",
                "title": {"fr": "Achète de l'Aura", "en": "Buy Aura", "pt": "Compra Aura"},
                "body": {
                    "fr": "Depuis le Portefeuille, choisis un pack d'Aura. L'Aura sert à soutenir les créateurs (tips, abonnements).",
                    "en": "From the Wallet, pick an Aura pack. Aura is used to support creators (tips, subscriptions).",
                    "pt": "Na Carteira, escolhe um pacote de Aura. A Aura serve para apoiar criadores (tips, assinaturas).",
                },
            },
            {
                "step_id": "set-tier",
                "title": {
                    "fr": "Configure ton abonnement",
                    "en": "Set up your subscription",
                    "pt": "Configura a tua assinatura",
                },
                "body": {
                    "fr": "Onglet Monétisation du studio : fixe le prix en Aura et les avantages de ton palier d'abonnement.",
                    "en": "Studio Monetization tab: set the Aura price and perks of your subscription tier.",
                    "pt": "Separador Monetização do estúdio: define o preço em Aura e os benefícios do teu nível.",
                },
            },
            {
                "step_id": "payout",
                "title": {
                    "fr": "Demande un retrait",
                    "en": "Request a payout",
                    "pt": "Pede um levantamento",
                },
                "body": {
                    "fr": "Tes gains s'accumulent dans ton Portefeuille. Demande un retrait quand tu atteins le seuil.",
                    "en": "Your earnings accumulate in your Wallet. Request a payout when you reach the threshold.",
                    "pt": "Os teus ganhos acumulam na Carteira. Pede um levantamento ao atingir o limite.",
                },
            },
        ],
    },
    {
        "slug": "moderation",
        "icon": "shield",
        "order": 4,
        "title": {
            "fr": "Modérer ta communauté",
            "en": "Moderate your community",
            "pt": "Modera a tua comunidade",
        },
        "desc": {
            "fr": "Garde un chat sain avec les outils de modération.",
            "en": "Keep a healthy chat with moderation tools.",
            "pt": "Mantém um chat saudável com as ferramentas de moderação.",
        },
        "steps": [
            {
                "step_id": "chat-tools",
                "title": {
                    "fr": "Actions rapides du chat",
                    "en": "Chat quick actions",
                    "pt": "Ações rápidas do chat",
                },
                "body": {
                    "fr": "En survolant un message (en tant que streamer), utilise les boutons Timeout, Shadow ban, Ban et Supprimer.",
                    "en": "Hovering a message (as the streamer), use the Timeout, Shadow ban, Ban and Delete buttons.",
                    "pt": "Ao passar o rato sobre uma mensagem (como streamer), usa os botões Timeout, Shadow ban, Ban e Apagar.",
                },
            },
            {
                "step_id": "bans",
                "title": {
                    "fr": "Gère les bannissements",
                    "en": "Manage bans",
                    "pt": "Gere os bans",
                },
                "body": {
                    "fr": "Onglet Communauté : consulte et lève les bans (utilisateurs, shadow, IP) actifs sur ta chaîne.",
                    "en": "Community tab: review and lift active bans (users, shadow, IP) on your channel.",
                    "pt": "Separador Comunidade: vê e levanta bans ativos (utilizadores, shadow, IP) no teu canal.",
                },
            },
            {
                "step_id": "words",
                "title": {
                    "fr": "Mots interdits & slow-mode",
                    "en": "Banned words & slow-mode",
                    "pt": "Palavras proibidas & slow-mode",
                },
                "body": {
                    "fr": "Utilise /slowmode et la liste de mots interdits pour limiter le spam et les abus.",
                    "en": "Use /slowmode and the banned words list to limit spam and abuse.",
                    "pt": "Usa /slowmode e a lista de palavras proibidas para limitar spam e abusos.",
                },
            },
        ],
    },
    {
        "slug": "security",
        "icon": "shield",
        "order": 5,
        "title": {
            "fr": "Sécuriser ton compte",
            "en": "Secure your account",
            "pt": "Proteger a tua conta",
        },
        "desc": {
            "fr": "Protège ton compte de créateur.",
            "en": "Protect your creator account.",
            "pt": "Protege a tua conta de criador.",
        },
        "steps": [
            {
                "step_id": "2fa",
                "title": {
                    "fr": "Active la double authentification",
                    "en": "Enable two-factor auth",
                    "pt": "Ativa a autenticação de dois fatores",
                },
                "body": {
                    "fr": "Dans Paramètres, active la 2FA (TOTP) en scannant le QR code et conserve tes codes de secours.",
                    "en": "In Settings, enable 2FA (TOTP) by scanning the QR code and keep your recovery codes.",
                    "pt": "Em Definições, ativa a 2FA (TOTP) lendo o QR code e guarda os códigos de recuperação.",
                },
            },
            {
                "step_id": "sessions",
                "title": {
                    "fr": "Vérifie tes appareils",
                    "en": "Review your devices",
                    "pt": "Revê os teus dispositivos",
                },
                "body": {
                    "fr": "Consulte tes appareils connectés et déconnecte ceux que tu ne reconnais pas.",
                    "en": "Check your connected devices and log out any you don't recognize.",
                    "pt": "Vê os dispositivos ligados e termina sessão nos que não reconheces.",
                },
            },
        ],
    },
]
