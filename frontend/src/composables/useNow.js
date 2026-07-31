import { ref } from 'vue'

// Gemeinsamer, minütlich aktualisierter Zeitstempel — damit Überfälligkeits-
// Markierungen auch ohne Neuladen der Seite aktuell bleiben.
const now = ref(Date.now())
setInterval(() => {
  now.value = Date.now()
}, 60_000)

export function useNow() {
  return now
}
