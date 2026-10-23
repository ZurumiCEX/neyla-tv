"use client";

// Signal global « le solde Aura a changé » (tip, abonnement, don, achat, retrait).
// Les composants affichant le solde (header, portefeuille) se rafraîchissent.

const EVENT = "neyla:wallet-changed";

export function notifyWalletChanged(): void {
  if (typeof window !== "undefined") window.dispatchEvent(new Event(EVENT));
}

export function onWalletChanged(handler: () => void): () => void {
  window.addEventListener(EVENT, handler);
  return () => window.removeEventListener(EVENT, handler);
}
