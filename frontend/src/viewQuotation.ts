export function openQuotationView(quoteNumber: string) {
  window.open(`/quote/${quoteNumber.toLowerCase()}`, "_blank");
}
