// Contenu des tutoriels (auto-suffisant, localisé FR/EN/PT).
// La progression ("acquis") est persistée via /api/guides/progress, par clé
// "<slug>:<stepId>".

import type { Locale } from "./messages";

export type GuideStep = { id: string; title: string; body: string };
export type Guide = {
  slug: string;
  icon: string;
  title: string;
  desc: string;
  steps: GuideStep[];
};

// Icônes (path SVG, stroke).
export const GUIDE_ICONS: Record<string, string> = {
  rocket: "M5 15l-2 6 6-2M9 11a6 6 0 016-6c3 0 4 1 4 4a6 6 0 01-6 6l-4 4-4-4 4-4zM14 8h.01",
  broadcast: "M4 12a8 8 0 018-8M4 12a8 8 0 008 8M12 12h.01M7 12a5 5 0 015-5M7 12a5 5 0 005 5",
  coins: "M12 8c-3 0-5 1-5 2.5S9 13 12 13s5 1 5 2.5S15 18 12 18m0-10c3 0 5 1 5 2.5M12 8V6m0 12v-2",
  shield: "M12 3l8 3v5c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6z",
};

const FR: Guide[] = [
  {
    slug: "getting-started",
    icon: "rocket",
    title: "Premiers pas",
    desc: "Crée ton compte et configure ton profil pour bien démarrer.",
    steps: [
      { id: "verify-email", title: "Vérifie ton adresse email", body: "Confirme ton email via le lien reçu pour débloquer toutes les fonctionnalités (chat, achats, notifications)." },
      { id: "profile", title: "Personnalise ton profil", body: "Dans Paramètres, ajoute un nom d'affichage, un avatar, une bannière, une bio, ton pays et tes réseaux sociaux." },
      { id: "follow", title: "Suis tes premières chaînes", body: "Parcours les lives et catégories, puis suis des créateurs : ils apparaîtront dans ta barre latérale et l'onglet Suivis." },
    ],
  },
  {
    slug: "streaming-setup",
    icon: "broadcast",
    title: "Configurer et démarrer le streaming",
    desc: "De la demande streamer à ton premier direct avec OBS.",
    steps: [
      { id: "apply", title: "Deviens streamer", body: "Depuis le Dashboard, fais une demande d'accès streamer. Une fois approuvée, ta clé RTMPS et les outils de diffusion se débloquent." },
      { id: "obs", title: "Configure OBS", body: "Dans l'onglet Diffusion, copie le serveur RTMPS et ta clé de stream. Dans OBS : Paramètres → Flux → Service « Personnalisé », colle serveur et clé." },
      { id: "infos", title: "Renseigne les infos du stream", body: "Onglet Aperçu : définis un titre, une catégorie et des tags pour rendre ton live découvrable." },
      { id: "golive", title: "Passe en direct", body: "Lance « Démarrer le streaming » dans OBS (ou le bouton Passer en direct pour une démo). Ton minuteur de session et tes spectateurs s'affichent en haut du studio." },
      { id: "overlay", title: "Ajoute l'overlay d'alertes", body: "Onglet Diffusion : copie l'URL de l'overlay et ajoute-la comme source navigateur dans OBS pour afficher followers, abos et tips en direct." },
    ],
  },
  {
    slug: "monetization",
    icon: "coins",
    title: "Monétisation",
    desc: "Aura, abonnements, tips et retraits.",
    steps: [
      { id: "buy-aura", title: "Achète de l'Aura", body: "Depuis le Portefeuille, choisis un pack d'Aura. L'Aura sert à soutenir les créateurs (tips, abonnements)." },
      { id: "set-tier", title: "Configure ton abonnement", body: "Onglet Monétisation du studio : fixe le prix en Aura et les avantages de ton palier d'abonnement." },
      { id: "payout", title: "Demande un retrait", body: "Tes gains s'accumulent dans ton Portefeuille. Demande un retrait quand tu atteins le seuil." },
    ],
  },
  {
    slug: "moderation",
    icon: "shield",
    title: "Modérer ta communauté",
    desc: "Garde un chat sain avec les outils de modération.",
    steps: [
      { id: "chat-tools", title: "Actions rapides du chat", body: "En survolant un message (en tant que streamer), utilise les boutons Timeout, Shadow ban, Ban et Supprimer." },
      { id: "bans", title: "Gère les bannissements", body: "Onglet Communauté : consulte et lève les bans (utilisateurs, shadow, IP) actifs sur ta chaîne." },
      { id: "words", title: "Mots interdits & slow-mode", body: "Utilise /slowmode et la liste de mots interdits pour limiter le spam et les abus." },
    ],
  },
  {
    slug: "security",
    icon: "shield",
    title: "Sécuriser ton compte",
    desc: "Protège ton compte de créateur.",
    steps: [
      { id: "2fa", title: "Active la double authentification", body: "Dans Paramètres, active la 2FA (TOTP) en scannant le QR code et conserve tes codes de secours." },
      { id: "sessions", title: "Vérifie tes appareils", body: "Consulte tes appareils connectés et déconnecte ceux que tu ne reconnais pas." },
    ],
  },
];

const EN: Guide[] = [
  {
    slug: "getting-started",
    icon: "rocket",
    title: "Getting started",
    desc: "Create your account and set up your profile.",
    steps: [
      { id: "verify-email", title: "Verify your email", body: "Confirm your email via the link you received to unlock all features (chat, purchases, notifications)." },
      { id: "profile", title: "Customize your profile", body: "In Settings, add a display name, avatar, banner, bio, country and social links." },
      { id: "follow", title: "Follow your first channels", body: "Browse lives and categories, then follow creators: they appear in your sidebar and the Following tab." },
    ],
  },
  {
    slug: "streaming-setup",
    icon: "broadcast",
    title: "Set up and start streaming",
    desc: "From streamer application to your first live with OBS.",
    steps: [
      { id: "apply", title: "Become a streamer", body: "From the Dashboard, request streamer access. Once approved, your RTMPS key and broadcast tools unlock." },
      { id: "obs", title: "Configure OBS", body: "In the Broadcast tab, copy the RTMPS server and your stream key. In OBS: Settings → Stream → Custom service, paste server and key." },
      { id: "infos", title: "Fill in stream info", body: "Overview tab: set a title, category and tags to make your stream discoverable." },
      { id: "golive", title: "Go live", body: "Start streaming in OBS (or the Go live button for a demo). Your session timer and viewers show at the top of the studio." },
      { id: "overlay", title: "Add the alerts overlay", body: "Broadcast tab: copy the overlay URL and add it as a browser source in OBS to show followers, subs and tips live." },
    ],
  },
  {
    slug: "monetization",
    icon: "coins",
    title: "Monetization",
    desc: "Aura, subscriptions, tips and payouts.",
    steps: [
      { id: "buy-aura", title: "Buy Aura", body: "From the Wallet, pick an Aura pack. Aura is used to support creators (tips, subscriptions)." },
      { id: "set-tier", title: "Set up your subscription", body: "Studio Monetization tab: set the Aura price and perks of your subscription tier." },
      { id: "payout", title: "Request a payout", body: "Your earnings accumulate in your Wallet. Request a payout when you reach the threshold." },
    ],
  },
  {
    slug: "moderation",
    icon: "shield",
    title: "Moderate your community",
    desc: "Keep a healthy chat with moderation tools.",
    steps: [
      { id: "chat-tools", title: "Chat quick actions", body: "Hovering a message (as the streamer), use the Timeout, Shadow ban, Ban and Delete buttons." },
      { id: "bans", title: "Manage bans", body: "Community tab: review and lift active bans (users, shadow, IP) on your channel." },
      { id: "words", title: "Banned words & slow-mode", body: "Use /slowmode and the banned words list to limit spam and abuse." },
    ],
  },
  {
    slug: "security",
    icon: "shield",
    title: "Secure your account",
    desc: "Protect your creator account.",
    steps: [
      { id: "2fa", title: "Enable two-factor auth", body: "In Settings, enable 2FA (TOTP) by scanning the QR code and keep your recovery codes." },
      { id: "sessions", title: "Review your devices", body: "Check your connected devices and log out any you don't recognize." },
    ],
  },
];

const PT: Guide[] = [
  {
    slug: "getting-started",
    icon: "rocket",
    title: "Primeiros passos",
    desc: "Cria a tua conta e configura o teu perfil.",
    steps: [
      { id: "verify-email", title: "Verifica o teu email", body: "Confirma o email pelo link recebido para desbloquear todas as funcionalidades (chat, compras, notificações)." },
      { id: "profile", title: "Personaliza o teu perfil", body: "Em Definições, adiciona nome, avatar, banner, bio, país e redes sociais." },
      { id: "follow", title: "Segue os teus primeiros canais", body: "Explora lives e categorias e segue criadores: aparecem na barra lateral e no separador Seguindo." },
    ],
  },
  {
    slug: "streaming-setup",
    icon: "broadcast",
    title: "Configurar e iniciar a transmissão",
    desc: "Do pedido de streamer à primeira transmissão com OBS.",
    steps: [
      { id: "apply", title: "Torna-te streamer", body: "No Painel, pede acesso de streamer. Após aprovação, a tua chave RTMPS e as ferramentas de transmissão são desbloqueadas." },
      { id: "obs", title: "Configura o OBS", body: "No separador Transmissão, copia o servidor RTMPS e a tua chave. No OBS: Definições → Transmissão → serviço Personalizado, cola servidor e chave." },
      { id: "infos", title: "Preenche as informações", body: "Separador Visão geral: define título, categoria e tags para o teu stream ser descoberto." },
      { id: "golive", title: "Fica ao vivo", body: "Inicia a transmissão no OBS (ou o botão Ficar ao vivo para demo). O cronómetro e os espectadores aparecem no topo do estúdio." },
      { id: "overlay", title: "Adiciona o overlay de alertas", body: "Separador Transmissão: copia o URL do overlay e adiciona-o como fonte de navegador no OBS para mostrar seguidores, assinantes e tips ao vivo." },
    ],
  },
  {
    slug: "monetization",
    icon: "coins",
    title: "Monetização",
    desc: "Aura, assinaturas, tips e levantamentos.",
    steps: [
      { id: "buy-aura", title: "Compra Aura", body: "Na Carteira, escolhe um pacote de Aura. A Aura serve para apoiar criadores (tips, assinaturas)." },
      { id: "set-tier", title: "Configura a tua assinatura", body: "Separador Monetização do estúdio: define o preço em Aura e os benefícios do teu nível." },
      { id: "payout", title: "Pede um levantamento", body: "Os teus ganhos acumulam na Carteira. Pede um levantamento ao atingir o limite." },
    ],
  },
  {
    slug: "moderation",
    icon: "shield",
    title: "Modera a tua comunidade",
    desc: "Mantém um chat saudável com as ferramentas de moderação.",
    steps: [
      { id: "chat-tools", title: "Ações rápidas do chat", body: "Ao passar o rato sobre uma mensagem (como streamer), usa os botões Timeout, Shadow ban, Ban e Apagar." },
      { id: "bans", title: "Gere os bans", body: "Separador Comunidade: vê e levanta bans ativos (utilizadores, shadow, IP) no teu canal." },
      { id: "words", title: "Palavras proibidas & slow-mode", body: "Usa /slowmode e a lista de palavras proibidas para limitar spam e abusos." },
    ],
  },
  {
    slug: "security",
    icon: "shield",
    title: "Protege a tua conta",
    desc: "Protege a tua conta de criador.",
    steps: [
      { id: "2fa", title: "Ativa a autenticação de dois fatores", body: "Em Definições, ativa a 2FA (TOTP) lendo o QR code e guarda os códigos de recuperação." },
      { id: "sessions", title: "Revê os teus dispositivos", body: "Vê os dispositivos ligados e termina sessão nos que não reconheces." },
    ],
  },
];

const BY_LOCALE: Record<Locale, Guide[]> = { fr: FR, en: EN, pt: PT };

export function getGuides(locale: Locale): Guide[] {
  return BY_LOCALE[locale] ?? FR;
}

export function getGuide(locale: Locale, slug: string): Guide | undefined {
  return getGuides(locale).find((g) => g.slug === slug);
}
