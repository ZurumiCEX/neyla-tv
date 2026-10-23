// Contenus des pages légales et institutionnelles (FR / EN / PT).
// ⚠️ Modèles de départ rédigés pour le MVP : à faire valider par un juriste
// (droit applicable, mentions de l'éditeur, autorité de protection des données)
// avant l'ouverture au public.

import type { Locale } from "./messages";

export type LegalSection = { id?: string; h: string; p: string[] };
export type LegalDoc = { title: string; intro?: string; sections: LegalSection[] };
export type LegalSlug =
  | "terms"
  | "privacy"
  | "cookies"
  | "guidelines"
  | "dmca"
  | "about"
  | "contact";

export const LEGAL_UPDATED_AT = "2026-10-23";

export const LEGAL_NAV: LegalSlug[] = [
  "terms",
  "privacy",
  "cookies",
  "guidelines",
  "dmca",
  "about",
  "contact",
];

const FR: Record<LegalSlug, LegalDoc> = {
  terms: {
    title: "Conditions générales d'utilisation",
    intro:
      "Les présentes conditions encadrent l'utilisation de Neyla TV, plateforme de diffusion en direct et de vidéos courtes dédiée aux créateurs d'Afrique de l'Ouest francophone. En créant un compte, tu les acceptes.",
    sections: [
      {
        h: "1. Accès au service et âge minimum",
        p: [
          "Neyla TV est réservée aux personnes âgées de 18 ans ou plus. Ta date de naissance est demandée à l'inscription ; une fausse déclaration entraîne la fermeture du compte.",
          "Le service est accessible gratuitement ; certaines fonctionnalités (Aura, abonnements, retraits) obéissent à des règles spécifiques décrites ci-dessous.",
        ],
      },
      {
        h: "2. Compte et sécurité",
        p: [
          "Tu es responsable de la confidentialité de ton mot de passe et de toute activité sur ton compte. Active la vérification en deux étapes dans tes paramètres.",
          "Un compte est personnel : la revente, le prêt ou l'usage de comptes multiples pour contourner une sanction ou manipuler les compteurs est interdit.",
        ],
      },
      {
        h: "3. Règles de conduite",
        p: [
          "Tu t'engages à respecter les Règles de la communauté. Les contenus illégaux, haineux, violents, à caractère sexuel ou mettant en danger autrui sont interdits.",
          "Neyla TV peut retirer un contenu, restreindre une fonctionnalité ou suspendre un compte en cas de manquement.",
        ],
      },
      {
        id: "partenaires",
        h: "4. Streamers (conditions partenaires)",
        p: [
          "Diffuser en direct nécessite une candidature approuvée. L'approbation donne accès à une clé de diffusion personnelle, à garder secrète.",
          "Le streamer est seul responsable de ses diffusions, y compris de la musique et des contenus de tiers qu'il utilise.",
          "Charity Day : chaque mois, les streamers participent au Charity Day en faisant un don en Aura au moins égal au montant plancher fixé pour l'événement, ou en organisant eux-mêmes un live caritatif. Aucun pourcentage de revenus n'est imposé.",
        ],
      },
      {
        id: "aura",
        h: "5. Aura (monnaie virtuelle)",
        p: [
          "L'Aura est une monnaie virtuelle propre à Neyla TV, achetée en FCFA (prix affiché avant paiement). Elle sert à soutenir les créateurs : tips, abonnements, dons Charity Day.",
          "L'Aura achetée n'est ni remboursable ni convertible en argent, sauf obligation légale. Seule l'Aura gagnée par un streamer approuvé (tips et abonnements reçus) peut faire l'objet d'un retrait.",
          "Commissions : 30 % sur les tips et abonnements (prélevés sur la part du créateur), 1 % sur les achats d'Aura effectués par un streamer, et des frais de traitement sur les retraits (3 % par défaut). Les taux en vigueur sont affichés dans le portefeuille.",
          "Les retraits sont versés sur un compte Wave ou Orange Money au nom du streamer, après confirmation par code e-mail. Un montant minimum s'applique. En cas de remboursement ou de contestation d'un achat, l'Aura correspondante est reprise et les retraits peuvent être suspendus pendant l'examen.",
        ],
      },
      {
        h: "6. Abonnements",
        p: [
          "Un abonnement à une chaîne est payé en Aura, pour une période d'un mois, et se renouvelle automatiquement au prix payé lors de la souscription.",
          "Tu peux annuler le renouvellement à tout moment : l'accès aux avantages reste ouvert jusqu'à la fin de la période déjà payée. Un abonnement offert ne se renouvelle pas automatiquement.",
        ],
      },
      {
        h: "7. Programme RSE",
        p: [
          "Une part de la commission plateforme — jamais la part des créateurs — finance des associations partenaires. Les montants collectés et reversés sont publiés sur la page Charity Day.",
        ],
      },
      {
        h: "8. Propriété intellectuelle",
        p: [
          "Tu restes titulaire de tes contenus. Tu accordes à Neyla TV une licence non exclusive, mondiale et gratuite pour les héberger, les diffuser et les promouvoir sur la plateforme, pour la durée de leur mise en ligne.",
          "Les signalements de violation de droits d'auteur suivent la procédure décrite dans la page Droits d'auteur.",
        ],
      },
      {
        h: "9. Responsabilité",
        p: [
          "Neyla TV met en œuvre des moyens raisonnables pour assurer la disponibilité du service, sans garantie d'absence d'interruption. La page Statut indique l'état des services en temps réel.",
          "Neyla TV n'est pas responsable des contenus publiés par les utilisateurs, mais agit promptement dès qu'un contenu manifestement illicite lui est signalé.",
        ],
      },
      {
        h: "10. Résiliation et modifications",
        p: [
          "Tu peux fermer ton compte à tout moment depuis tes paramètres ou en contactant le support. L'Aura gagnée et retirable doit être retirée avant la fermeture.",
          "Ces conditions peuvent évoluer ; les changements importants sont annoncés sur la plateforme au moins 15 jours avant leur entrée en vigueur.",
        ],
      },
      {
        h: "11. Contact",
        p: [
          "Pour toute question relative à ces conditions : legal@neyla.tv (voir aussi la page Contact).",
        ],
      },
    ],
  },
  privacy: {
    title: "Politique de confidentialité",
    intro:
      "Cette politique explique quelles données Neyla TV collecte, pourquoi, combien de temps elles sont conservées et comment exercer tes droits.",
    sections: [
      {
        h: "Données collectées",
        p: [
          "Compte : e-mail, nom d'utilisateur, date de naissance, mot de passe (stocké chiffré, jamais en clair), photo et biographie facultatives.",
          "Activité : chaînes suivies, messages de chat, tips, abonnements, dons, historique de diffusion, adresses IP de connexion (sécurité et lutte contre la fraude).",
          "Paiements : montants, moyen de paiement choisi et référence de transaction. Les données de carte sont traitées par le prestataire de paiement, jamais par Neyla TV. Pour les retraits : numéro Wave ou Orange Money.",
        ],
      },
      {
        h: "Finalités",
        p: [
          "Fournir le service (comptes, diffusion, chat, Aura), sécuriser la plateforme (anti-fraude, anti-spam, modération), respecter nos obligations légales et comptables, et améliorer le produit à partir de statistiques agrégées.",
          "Nous n'utilisons pas tes données pour de la publicité ciblée et ne les vendons pas.",
        ],
      },
      {
        h: "Sous-traitants",
        p: [
          "Bunny Stream (hébergement et diffusion vidéo), Cloudflare (stockage d'images, protection anti-robots), prestataires de paiement (Stripe, Wave, Orange Money), hébergeur de l'application et service d'envoi d'e-mails. Chacun n'accède qu'aux données nécessaires à sa mission.",
        ],
      },
      {
        h: "Conservation",
        p: [
          "Les données de compte sont conservées tant que le compte est actif, puis supprimées ou anonymisées dans un délai de 30 jours après sa fermeture, sauf obligation légale (données financières : 10 ans).",
          "Les messages de chat sont éphémères et ne sont pas archivés au-delà de l'historique récent de la chaîne.",
        ],
      },
      {
        h: "Tes droits",
        p: [
          "Tu peux accéder à tes données, les rectifier, demander leur suppression ou leur portabilité, et t'opposer à certains traitements, en écrivant à privacy@neyla.tv. Nous répondons sous 30 jours.",
          "Tu peux également saisir l'autorité de protection des données personnelles de ton pays.",
        ],
      },
      {
        h: "Sécurité",
        p: [
          "Mots de passe chiffrés (Argon2), connexions HTTPS, vérification en deux étapes, codes de confirmation pour les retraits, journal d'audit des actions sensibles.",
        ],
      },
    ],
  },
  cookies: {
    title: "Politique cookies",
    intro:
      "Neyla TV utilise un nombre minimal de cookies et de stockages locaux, tous nécessaires au fonctionnement du service.",
    sections: [
      {
        h: "Ce que nous utilisons",
        p: [
          "Cookie de session sécurisé (HttpOnly) : te garde connecté de manière sûre.",
          "Préférences stockées dans ton navigateur : langue, thème clair/sombre, menu replié, annonces déjà fermées.",
          "Protection anti-robots (Cloudflare Turnstile) lors de l'inscription.",
        ],
      },
      {
        h: "Ce que nous n'utilisons pas",
        p: ["Aucun cookie publicitaire ni traceur de réseaux sociaux tiers."],
      },
      {
        h: "Gérer les cookies",
        p: [
          "Tu peux supprimer cookies et données locales depuis les réglages de ton navigateur. La suppression du cookie de session te déconnecte.",
        ],
      },
    ],
  },
  guidelines: {
    title: "Règles de la communauté",
    intro:
      "Neyla TV est un espace de partage, de jeu et de soutien. Ces règles protègent la communauté ; elles s'appliquent aux lives, aux vidéos Instant, au chat et aux profils.",
    sections: [
      {
        h: "Respect",
        p: [
          "Pas de harcèlement, d'insultes, de menaces ni de propos haineux visant une personne ou un groupe (origine, religion, genre, orientation, handicap…).",
        ],
      },
      {
        h: "Contenus interdits",
        p: [
          "Nudité et contenus sexuels, violence réelle ou gore, apologie du terrorisme, activités illégales, mise en danger de soi ou d'autrui, informations personnelles d'autrui (doxxing), arnaques et jeux d'argent non autorisés.",
        ],
      },
      {
        h: "Intégrité de la plateforme",
        p: [
          "Interdits : faux spectateurs, robots, comptes multiples, auto-tips ou échanges d'Aura entre comptes liés, spam et liens malveillants. Ces pratiques entraînent le gel des retraits et la suspension du compte.",
        ],
      },
      {
        h: "Droits d'auteur",
        p: ["Ne diffuse que des contenus (musique, films, matchs) que tu as le droit d'utiliser."],
      },
      {
        h: "Sanctions et signalement",
        p: [
          "Selon la gravité : retrait du contenu, avertissement, mise en sourdine dans le chat, suspension temporaire, fermeture définitive.",
          "Utilise le bouton « Signaler » sur une chaîne ou un message ; l'équipe de modération examine chaque signalement.",
        ],
      },
    ],
  },
  dmca: {
    title: "Droits d'auteur",
    intro:
      "Neyla TV respecte la propriété intellectuelle et retire promptement les contenus contrefaisants qui lui sont signalés.",
    sections: [
      {
        h: "Signaler une violation",
        p: [
          "Écris à copyright@neyla.tv en indiquant : ton identité et tes coordonnées, l'œuvre protégée, l'URL exacte du contenu litigieux, une déclaration de bonne foi et une déclaration sur l'exactitude des informations.",
        ],
      },
      {
        h: "Contre-notification",
        p: [
          "Si ton contenu a été retiré par erreur, tu peux répondre au même adresse en expliquant pourquoi tu disposes des droits nécessaires.",
        ],
      },
      {
        h: "Récidive",
        p: ["Les comptes faisant l'objet de violations répétées sont fermés."],
      },
    ],
  },
  about: {
    title: "À propos de Neyla TV",
    intro: "Stream, gagne ta vie, change la tienne et celle des autres.",
    sections: [
      {
        h: "Notre mission",
        p: [
          "Neyla TV est une plateforme de streaming pensée pour l'Afrique de l'Ouest francophone : jeux vidéo, discussions, musique, créativité et vie quotidienne.",
          "Notre objectif est l'inclusion financière des créateurs : recevoir des tips et des abonnements en Aura, puis retirer ses gains sur Wave ou Orange Money.",
        ],
      },
      {
        h: "Un engagement social",
        p: [
          "Chaque mois, le Charity Day réunit la communauté au profit d'associations partenaires. Les montants collectés et reversés sont publiés en toute transparence.",
        ],
      },
      {
        h: "Rejoindre l'aventure",
        p: ["Tu veux streamer ? Dépose ta candidature depuis la page « Devenir streamer »."],
      },
    ],
  },
  contact: {
    title: "Contact",
    intro: "Une question, un partenariat, une demande presse ? Écris-nous.",
    sections: [
      {
        h: "Adresses",
        p: [
          "Support utilisateurs : support@neyla.tv",
          "Partenariats & créateurs : partners@neyla.tv",
          "Presse : press@neyla.tv",
          "Questions juridiques : legal@neyla.tv · Données personnelles : privacy@neyla.tv · Droits d'auteur : copyright@neyla.tv",
        ],
      },
      {
        h: "Depuis ton compte",
        p: [
          "Connecté, tu peux aussi suivre les messages de l'équipe dans ta boîte de réception et signaler un contenu directement depuis une chaîne.",
        ],
      },
    ],
  },
};

const EN: Record<LegalSlug, LegalDoc> = {
  terms: {
    title: "Terms of Service",
    intro:
      "These terms govern the use of Neyla TV, a live streaming and short-video platform for creators in French-speaking West Africa. By creating an account, you accept them.",
    sections: [
      {
        h: "1. Access and minimum age",
        p: [
          "Neyla TV is reserved for people aged 18 or over. Your date of birth is requested at sign-up; a false statement leads to account closure.",
          "The service is free to use; some features (Aura, subscriptions, withdrawals) follow the specific rules below.",
        ],
      },
      {
        h: "2. Account and security",
        p: [
          "You are responsible for keeping your password confidential and for all activity on your account. Enable two-step verification in your settings.",
          "Accounts are personal: selling or lending them, or using several accounts to evade a sanction or inflate counters, is forbidden.",
        ],
      },
      {
        h: "3. Conduct",
        p: [
          "You agree to follow the Community Guidelines. Illegal, hateful, violent or sexual content, or content endangering others, is forbidden.",
          "Neyla TV may remove content, restrict features or suspend an account in case of breach.",
        ],
      },
      {
        id: "partenaires",
        h: "4. Streamers (partner terms)",
        p: [
          "Going live requires an approved application. Approval grants a personal stream key, which must be kept secret.",
          "Streamers are solely responsible for their broadcasts, including any third-party music or content they use.",
          "Charity Day: every month, streamers take part by donating at least the event's minimum amount in Aura, or by hosting a charity live themselves. No share of revenue is imposed.",
        ],
      },
      {
        id: "aura",
        h: "5. Aura (virtual currency)",
        p: [
          "Aura is Neyla TV's virtual currency, bought in FCFA (price shown before payment). It is used to support creators: tips, subscriptions and Charity Day donations.",
          "Purchased Aura is neither refundable nor convertible into money, except where required by law. Only Aura earned by an approved streamer (tips and subscriptions received) can be withdrawn.",
          "Fees: 30% on tips and subscriptions (taken from the creator's share), 1% on Aura purchases made by a streamer, and a processing fee on withdrawals (3% by default). Current rates are shown in the wallet.",
          "Withdrawals are paid to a Wave or Orange Money account in the streamer's name, after confirmation by an email code. A minimum amount applies. If a purchase is refunded or disputed, the corresponding Aura is taken back and withdrawals may be put on hold during review.",
        ],
      },
      {
        h: "6. Subscriptions",
        p: [
          "A channel subscription is paid in Aura for one month and renews automatically at the price paid when subscribing.",
          "You can cancel renewal at any time: perks stay available until the end of the paid period. Gifted subscriptions do not renew automatically.",
        ],
      },
      {
        h: "7. CSR program",
        p: [
          "Part of the platform commission — never the creators' share — funds partner charities. Amounts collected and paid out are published on the Charity Day page.",
        ],
      },
      {
        h: "8. Intellectual property",
        p: [
          "You keep ownership of your content. You grant Neyla TV a non-exclusive, worldwide, royalty-free licence to host, broadcast and promote it on the platform while it is online.",
          "Copyright reports follow the procedure described on the Copyright page.",
        ],
      },
      {
        h: "9. Liability",
        p: [
          "Neyla TV takes reasonable steps to keep the service available but does not guarantee it will be uninterrupted. The Status page shows live service health.",
          "Neyla TV is not responsible for user content, but acts promptly once clearly illegal content is reported.",
        ],
      },
      {
        h: "10. Termination and changes",
        p: [
          "You can close your account at any time from your settings or by contacting support. Withdraw any earned Aura before closing.",
          "These terms may change; significant changes are announced on the platform at least 15 days before they take effect.",
        ],
      },
      {
        h: "11. Contact",
        p: ["Questions about these terms: legal@neyla.tv (see also the Contact page)."],
      },
    ],
  },
  privacy: {
    title: "Privacy Policy",
    intro:
      "This policy explains what data Neyla TV collects, why, how long it is kept and how to exercise your rights.",
    sections: [
      {
        h: "Data we collect",
        p: [
          "Account: email, username, date of birth, password (stored hashed, never in plain text), optional photo and bio.",
          "Activity: followed channels, chat messages, tips, subscriptions, donations, broadcast history, login IP addresses (security and fraud prevention).",
          "Payments: amounts, chosen payment method and transaction reference. Card data is handled by the payment provider, never by Neyla TV. For withdrawals: your Wave or Orange Money number.",
        ],
      },
      {
        h: "Purposes",
        p: [
          "To provide the service (accounts, streaming, chat, Aura), keep the platform safe (anti-fraud, anti-spam, moderation), meet legal and accounting obligations, and improve the product using aggregated statistics.",
          "We do not use your data for targeted advertising and we do not sell it.",
        ],
      },
      {
        h: "Processors",
        p: [
          "Bunny Stream (video hosting and delivery), Cloudflare (image storage, bot protection), payment providers (Stripe, Wave, Orange Money), our application host and email provider. Each only accesses the data it needs.",
        ],
      },
      {
        h: "Retention",
        p: [
          "Account data is kept while the account is active, then deleted or anonymised within 30 days of closure, unless the law requires otherwise (financial records: 10 years).",
          "Chat messages are ephemeral and not archived beyond the channel's recent history.",
        ],
      },
      {
        h: "Your rights",
        p: [
          "You can access, correct, delete or export your data, and object to some processing, by writing to privacy@neyla.tv. We reply within 30 days.",
          "You may also contact your country's data protection authority.",
        ],
      },
      {
        h: "Security",
        p: [
          "Hashed passwords (Argon2), HTTPS, two-step verification, confirmation codes for withdrawals, and an audit log of sensitive actions.",
        ],
      },
    ],
  },
  cookies: {
    title: "Cookie Policy",
    intro:
      "Neyla TV uses a minimal set of cookies and local storage, all required for the service to work.",
    sections: [
      {
        h: "What we use",
        p: [
          "Secure session cookie (HttpOnly): keeps you safely logged in.",
          "Preferences stored in your browser: language, light/dark theme, collapsed menu, dismissed announcements.",
          "Bot protection (Cloudflare Turnstile) at sign-up.",
        ],
      },
      { h: "What we don't use", p: ["No advertising cookies and no third-party social trackers."] },
      {
        h: "Managing cookies",
        p: [
          "You can delete cookies and local data from your browser settings. Deleting the session cookie logs you out.",
        ],
      },
    ],
  },
  guidelines: {
    title: "Community Guidelines",
    intro:
      "Neyla TV is a place to share, play and support each other. These rules protect the community across lives, Shorts, chat and profiles.",
    sections: [
      {
        h: "Respect",
        p: [
          "No harassment, insults, threats or hate speech targeting a person or group (origin, religion, gender, orientation, disability…).",
        ],
      },
      {
        h: "Prohibited content",
        p: [
          "Nudity and sexual content, real or graphic violence, support for terrorism, illegal activities, endangering yourself or others, sharing others' personal data (doxxing), scams and unauthorised gambling.",
        ],
      },
      {
        h: "Platform integrity",
        p: [
          "Forbidden: fake viewers, bots, multiple accounts, self-tipping or trading Aura between linked accounts, spam and malicious links. These lead to frozen withdrawals and account suspension.",
        ],
      },
      {
        h: "Copyright",
        p: ["Only stream content (music, films, matches) you have the right to use."],
      },
      {
        h: "Sanctions and reporting",
        p: [
          "Depending on severity: content removal, warning, chat timeout, temporary suspension, permanent ban.",
          "Use the “Report” button on a channel or message; the moderation team reviews every report.",
        ],
      },
    ],
  },
  dmca: {
    title: "Copyright",
    intro:
      "Neyla TV respects intellectual property and promptly removes infringing content reported to it.",
    sections: [
      {
        h: "Reporting an infringement",
        p: [
          "Email copyright@neyla.tv with: your identity and contact details, the protected work, the exact URL of the infringing content, a good-faith statement and a statement that the information is accurate.",
        ],
      },
      {
        h: "Counter-notice",
        p: [
          "If your content was removed by mistake, reply to the same address explaining why you hold the necessary rights.",
        ],
      },
      { h: "Repeat infringers", p: ["Accounts with repeated infringements are closed."] },
    ],
  },
  about: {
    title: "About Neyla TV",
    intro: "Stream, earn a living, change your life and others'.",
    sections: [
      {
        h: "Our mission",
        p: [
          "Neyla TV is a streaming platform built for French-speaking West Africa: gaming, talk shows, music, creativity and everyday life.",
          "Our goal is financial inclusion for creators: receive tips and subscriptions in Aura, then withdraw earnings to Wave or Orange Money.",
        ],
      },
      {
        h: "A social commitment",
        p: [
          "Every month, Charity Day brings the community together for partner charities. Amounts collected and paid out are published transparently.",
        ],
      },
      { h: "Join us", p: ["Want to stream? Apply from the “Become a streamer” page."] },
    ],
  },
  contact: {
    title: "Contact",
    intro: "A question, a partnership, a press request? Write to us.",
    sections: [
      {
        h: "Addresses",
        p: [
          "User support: support@neyla.tv",
          "Partnerships & creators: partners@neyla.tv",
          "Press: press@neyla.tv",
          "Legal: legal@neyla.tv · Personal data: privacy@neyla.tv · Copyright: copyright@neyla.tv",
        ],
      },
      {
        h: "From your account",
        p: [
          "When logged in, you can also read team messages in your inbox and report content directly from a channel.",
        ],
      },
    ],
  },
};

const PT: Record<LegalSlug, LegalDoc> = {
  terms: {
    title: "Termos de utilização",
    intro:
      "Estes termos regem a utilização da Neyla TV, plataforma de transmissões ao vivo e vídeos curtos para criadores da África Ocidental francófona. Ao criares uma conta, aceita-los.",
    sections: [
      {
        h: "1. Acesso e idade mínima",
        p: [
          "A Neyla TV é reservada a maiores de 18 anos. A data de nascimento é pedida no registo; uma declaração falsa leva ao encerramento da conta.",
          "O serviço é gratuito; algumas funcionalidades (Aura, assinaturas, levantamentos) seguem as regras abaixo.",
        ],
      },
      {
        h: "2. Conta e segurança",
        p: [
          "És responsável pela confidencialidade da tua palavra-passe e por toda a atividade na tua conta. Ativa a verificação em dois passos nas definições.",
          "A conta é pessoal: vender, emprestar ou usar várias contas para contornar sanções ou inflacionar contadores é proibido.",
        ],
      },
      {
        h: "3. Regras de conduta",
        p: [
          "Comprometes-te a respeitar as Regras da comunidade. Conteúdos ilegais, de ódio, violentos, sexuais ou que ponham outros em perigo são proibidos.",
          "A Neyla TV pode remover conteúdos, restringir funcionalidades ou suspender contas em caso de incumprimento.",
        ],
      },
      {
        id: "partenaires",
        h: "4. Streamers (termos de parceiro)",
        p: [
          "Transmitir ao vivo exige uma candidatura aprovada, que dá acesso a uma chave de transmissão pessoal e secreta.",
          "O streamer é o único responsável pelas suas transmissões, incluindo música e conteúdos de terceiros.",
          "Charity Day: todos os meses, os streamers participam doando em Aura pelo menos o montante mínimo do evento, ou organizando eles próprios um direto solidário. Nenhuma percentagem de receitas é imposta.",
        ],
      },
      {
        id: "aura",
        h: "5. Aura (moeda virtual)",
        p: [
          "A Aura é a moeda virtual da Neyla TV, comprada em FCFA (preço indicado antes do pagamento). Serve para apoiar criadores: gorjetas, assinaturas e doações do Charity Day.",
          "A Aura comprada não é reembolsável nem convertível em dinheiro, salvo obrigação legal. Só a Aura ganha por um streamer aprovado (gorjetas e assinaturas recebidas) pode ser levantada.",
          "Comissões: 30% sobre gorjetas e assinaturas (sobre a parte do criador), 1% sobre compras de Aura feitas por um streamer e uma taxa de processamento nos levantamentos (3% por defeito).",
          "Os levantamentos são pagos numa conta Wave ou Orange Money em nome do streamer, após confirmação por código enviado por e-mail. Aplica-se um montante mínimo. Em caso de reembolso ou contestação de uma compra, a Aura correspondente é retirada e os levantamentos podem ser suspensos durante a análise.",
        ],
      },
      {
        h: "6. Assinaturas",
        p: [
          "Uma assinatura de canal é paga em Aura por um mês e renova automaticamente ao preço pago na subscrição.",
          "Podes cancelar a renovação a qualquer momento: as vantagens mantêm-se até ao fim do período pago. As assinaturas oferecidas não renovam automaticamente.",
        ],
      },
      {
        h: "7. Programa RSE",
        p: [
          "Parte da comissão da plataforma — nunca a parte dos criadores — financia associações parceiras. Os montantes recolhidos e repassados são publicados na página Charity Day.",
        ],
      },
      {
        h: "8. Propriedade intelectual",
        p: [
          "Manténs a titularidade dos teus conteúdos e concedes à Neyla TV uma licença não exclusiva, mundial e gratuita para os alojar, transmitir e promover enquanto estiverem online.",
        ],
      },
      {
        h: "9. Responsabilidade",
        p: [
          "A Neyla TV faz esforços razoáveis para manter o serviço disponível, sem garantia de ausência de interrupções. A página Estado mostra a saúde dos serviços em tempo real.",
        ],
      },
      {
        h: "10. Encerramento e alterações",
        p: [
          "Podes encerrar a conta a qualquer momento. Levanta a Aura ganha antes do encerramento.",
          "Alterações importantes são anunciadas na plataforma pelo menos 15 dias antes de entrarem em vigor.",
        ],
      },
      { h: "11. Contacto", p: ["Questões sobre estes termos: legal@neyla.tv."] },
    ],
  },
  privacy: {
    title: "Política de privacidade",
    intro:
      "Esta política explica que dados a Neyla TV recolhe, porquê, durante quanto tempo e como exercer os teus direitos.",
    sections: [
      {
        h: "Dados recolhidos",
        p: [
          "Conta: e-mail, nome de utilizador, data de nascimento, palavra-passe (guardada cifrada), foto e biografia opcionais.",
          "Atividade: canais seguidos, mensagens de chat, gorjetas, assinaturas, doações, histórico de transmissões, endereços IP (segurança e antifraude).",
          "Pagamentos: montantes, meio de pagamento e referência. Os dados de cartão são tratados pelo prestador de pagamento. Para levantamentos: número Wave ou Orange Money.",
        ],
      },
      {
        h: "Finalidades",
        p: [
          "Fornecer o serviço, proteger a plataforma (antifraude, antispam, moderação), cumprir obrigações legais e melhorar o produto com estatísticas agregadas. Não vendemos os teus dados nem fazemos publicidade direcionada.",
        ],
      },
      {
        h: "Subcontratantes",
        p: [
          "Bunny Stream (vídeo), Cloudflare (imagens, proteção anti-robôs), prestadores de pagamento (Stripe, Wave, Orange Money), alojamento e envio de e-mails.",
        ],
      },
      {
        h: "Conservação",
        p: [
          "Dados de conta conservados enquanto a conta estiver ativa e apagados ou anonimizados 30 dias após o encerramento, salvo obrigação legal (dados financeiros: 10 anos).",
        ],
      },
      {
        h: "Os teus direitos",
        p: [
          "Acesso, retificação, apagamento, portabilidade e oposição: escreve para privacy@neyla.tv. Respondemos em 30 dias.",
        ],
      },
      {
        h: "Segurança",
        p: [
          "Palavras-passe cifradas (Argon2), HTTPS, verificação em dois passos, códigos de confirmação nos levantamentos.",
        ],
      },
    ],
  },
  cookies: {
    title: "Política de cookies",
    intro:
      "A Neyla TV usa um conjunto mínimo de cookies e armazenamento local, todos necessários ao funcionamento do serviço.",
    sections: [
      {
        h: "O que usamos",
        p: [
          "Cookie de sessão seguro (HttpOnly) para manter a sessão.",
          "Preferências no navegador: idioma, tema, menu recolhido, anúncios fechados.",
          "Proteção anti-robôs (Cloudflare Turnstile) no registo.",
        ],
      },
      {
        h: "O que não usamos",
        p: ["Nenhum cookie publicitário nem rastreadores de redes sociais."],
      },
      {
        h: "Gerir cookies",
        p: ["Podes apagar cookies e dados locais nas definições do navegador."],
      },
    ],
  },
  guidelines: {
    title: "Regras da comunidade",
    intro:
      "A Neyla TV é um espaço de partilha, jogo e apoio. Estas regras aplicam-se aos diretos, Instantes, chat e perfis.",
    sections: [
      { h: "Respeito", p: ["Proibido assédio, insultos, ameaças e discurso de ódio."] },
      {
        h: "Conteúdos proibidos",
        p: [
          "Nudez e conteúdo sexual, violência real, apologia do terrorismo, atividades ilegais, divulgação de dados pessoais de terceiros, burlas e jogos de azar não autorizados.",
        ],
      },
      {
        h: "Integridade da plataforma",
        p: [
          "Proibidos: espectadores falsos, bots, contas múltiplas, auto-gorjetas, spam. Estas práticas levam ao bloqueio dos levantamentos e à suspensão da conta.",
        ],
      },
      { h: "Direitos de autor", p: ["Transmite apenas conteúdos que tens direito de usar."] },
      {
        h: "Sanções e denúncias",
        p: ["Remoção, aviso, silenciamento, suspensão ou encerramento. Usa o botão «Denunciar»."],
      },
    ],
  },
  dmca: {
    title: "Direitos de autor",
    intro:
      "A Neyla TV respeita a propriedade intelectual e remove rapidamente conteúdos infratores que lhe sejam denunciados.",
    sections: [
      {
        h: "Denunciar uma infração",
        p: [
          "Escreve para copyright@neyla.tv com a tua identificação, a obra protegida, o URL exato do conteúdo e uma declaração de boa-fé.",
        ],
      },
      {
        h: "Contra-notificação",
        p: ["Se o teu conteúdo foi removido por engano, responde para o mesmo endereço."],
      },
      { h: "Reincidência", p: ["Contas com infrações repetidas são encerradas."] },
    ],
  },
  about: {
    title: "Sobre a Neyla TV",
    intro: "Transmite, ganha a vida, muda a tua e a dos outros.",
    sections: [
      {
        h: "A nossa missão",
        p: [
          "A Neyla TV é uma plataforma de streaming pensada para a África Ocidental francófona: jogos, conversas, música, criatividade e vida quotidiana.",
          "O nosso objetivo é a inclusão financeira dos criadores: receber gorjetas e assinaturas em Aura e levantar os ganhos em Wave ou Orange Money.",
        ],
      },
      {
        h: "Um compromisso social",
        p: [
          "Todos os meses, o Charity Day reúne a comunidade em favor de associações parceiras, com total transparência.",
        ],
      },
      {
        h: "Junta-te a nós",
        p: ["Queres transmitir? Candidata-te na página «Tornar-se streamer»."],
      },
    ],
  },
  contact: {
    title: "Contacto",
    intro: "Uma questão, uma parceria, um pedido de imprensa? Escreve-nos.",
    sections: [
      {
        h: "Endereços",
        p: [
          "Suporte: support@neyla.tv",
          "Parcerias e criadores: partners@neyla.tv",
          "Imprensa: press@neyla.tv",
          "Jurídico: legal@neyla.tv · Dados pessoais: privacy@neyla.tv · Direitos de autor: copyright@neyla.tv",
        ],
      },
    ],
  },
};

export const LEGAL: Record<Locale, Record<LegalSlug, LegalDoc>> = { fr: FR, en: EN, pt: PT };
