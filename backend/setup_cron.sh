#!/bin/bash
# Script pour configurer le cron job de rafraîchissement des données

echo "🔧 Configuration du cron job pour le rafraîchissement automatique des données..."

# Créer le script cron
cat > /app/run_refresh.sh << 'EOF'
#!/bin/bash
cd /app
python force_refresh_data.py >> /var/log/data_refresh.log 2>&1
EOF

chmod +x /app/run_refresh.sh

# Ajouter au crontab (toutes les 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /app/run_refresh.sh") | crontab -

echo "✅ Cron job configuré! Les données seront actualisées automatiquement toutes les 5 minutes."
echo "📝 Logs disponibles dans /var/log/data_refresh.log"

# Afficher le crontab pour confirmation
echo ""
echo "Crontab actuel:"
crontab -l
