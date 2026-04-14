// Wird im Production-Container durch docker-entrypoint.sh überschrieben.
// Im lokalen Dev-Betrieb bleibt dieses File leer – die App fällt dann auf
// import.meta.env (Vite .env-Dateien) zurück.
window.__env__ = {}
