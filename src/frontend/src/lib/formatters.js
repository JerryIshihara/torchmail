export function scoreTextClass(score) {
  if (score > 70) {
    return "text-emerald-700";
  }
  if (score > 40) {
    return "text-amber-700";
  }
  return "text-rose-700";
}

export function scorePillClass(score) {
  if (score > 70) {
    return "bg-emerald-100 text-emerald-800 ring-emerald-200";
  }
  if (score > 40) {
    return "bg-amber-100 text-amber-800 ring-amber-200";
  }
  return "bg-rose-100 text-rose-800 ring-rose-200";
}

export function countryFlag(code) {
  if (!code || code.length !== 2) {
    return "🏳️";
  }
  return code
    .toUpperCase()
    .split("")
    .map((char) => String.fromCodePoint(127397 + char.charCodeAt(0)))
    .join("");
}

export function prettyHiringParagraph(paragraph) {
  if (!paragraph || paragraph === "No active hiring page found") {
    return "No hiring info found.";
  }
  return paragraph;
}
