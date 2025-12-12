/**
 * Auto Activity Tracker - Tracking AUTOMATIQUE
 * Aucune modification des jeux nécessaire !
 */

(function() {
    'use strict';
    
    // Détecter automatiquement l'enfant_id et le jeu depuis l'URL
    const urlParts = window.location.pathname.split('/');
    let enfantId = null;
    let jeuName = null;
    
    // Extraire enfant_id (format : /jeu/enfant/123/animaux/)
    const enfantIndex = urlParts.indexOf('enfant');
    if (enfantIndex !== -1 && urlParts[enfantIndex + 1]) {
        enfantId = urlParts[enfantIndex + 1];
    }
    
    // Détecter le nom du jeu depuis l'URL
    const jeuPatterns = {
        'memory': /memory/i,
        'compter_3': /compter.*3/i,
        'compter_10': /compter.*10/i,
        'couleurs': /couleur/i,
        'emotions': /emotion/i,
        'memory_fruits': /memory.*fruit/i,
        'jours_semaine': /jour|semaine/i,
        'animaux': /animaux/i,
        'fruits': /fruits/i,
        'memory_couleurs': /memory.*couleur/i,
        'saisons': /saison/i,
        'puzzle': /puzzle/i,
        'labyrinthe': /labyrinthe/i,
    };
    
    // Trouver le jeu correspondant
    for (const [key, pattern] of Object.entries(jeuPatterns)) {
        if (pattern.test(window.location.pathname)) {
            jeuName = key;
            break;
        }
    }
    
    // Si on n'a pas trouvé l'enfant_id, essayer depuis une balise meta ou data
    if (!enfantId) {
        const metaEnfant = document.querySelector('meta[name="enfant-id"]');
        if (metaEnfant) {
            enfantId = metaEnfant.content;
        }
    }
    
    // Si pas de jeu détecté, essayer depuis le titre de la page
    if (!jeuName) {
        const title = document.title.toLowerCase();
        for (const [key, pattern] of Object.entries(jeuPatterns)) {
            if (pattern.test(title)) {
                jeuName = key;
                break;
            }
        }
    }
    
    // Vérifier qu'on a les infos nécessaires
    if (!enfantId || !jeuName) {
        console.log('ℹ️ Tracking désactivé (pas de jeu détecté)');
        return;
    }
    
    console.log('🎮 Auto-tracking activé:', jeuName, 'pour enfant', enfantId);
    
    // Variables de tracking
    let activiteId = null;
    let startTime = Date.now();
    let hasStarted = false;
    
    // Fonction pour démarrer l'activité
    async function startActivity() {
        if (hasStarted) return;
        hasStarted = true;
        
        try {
            const response = await fetch('/api/start-activity/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    enfant_id: enfantId,
                    jeu: jeuName
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                activiteId = data.activite_id;
                console.log('✅ Activité démarrée automatiquement, ID:', activiteId);
            }
        } catch (error) {
            console.error('❌ Erreur démarrage:', error);
        }
    }
    
    // Fonction pour terminer l'activité
    async function endActivity() {
        if (!activiteId) return;
        
        try {
            // Calculer la durée en minutes
            const durationMinutes = Math.round((Date.now() - startTime) / 1000 / 60);
            
            // Score estimé : si durée > 2 min, on considère que c'est réussi
            const reussi = durationMinutes >= 2;
            const score = reussi ? 75 : 50; // Score estimé
            
            const response = await fetch('/api/end-activity/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    activite_id: activiteId,
                    score: score,
                    reussi: reussi
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('✅ Activité terminée automatiquement');
                console.log(`   Durée: ${durationMinutes} minutes`);
            }
        } catch (error) {
            console.error('❌ Erreur fin activité:', error);
        }
    }
    
    // Démarrer dès que la page est chargée
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startActivity);
    } else {
        startActivity();
    }
    
    // Terminer quand l'utilisateur quitte
    window.addEventListener('beforeunload', function() {
        if (activiteId) {
            const durationMinutes = Math.round((Date.now() - startTime) / 1000 / 60);
            const reussi = durationMinutes >= 2;
            
            // Utiliser sendBeacon pour garantir l'envoi
            const data = JSON.stringify({
                activite_id: activiteId,
                score: reussi ? 75 : 50,
                reussi: reussi
            });
            
            navigator.sendBeacon('/api/end-activity/', data);
        }
    });
    
    // Terminer aussi après 30 secondes d'inactivité
    let inactivityTimer;
    
    function resetInactivityTimer() {
        clearTimeout(inactivityTimer);
        inactivityTimer = setTimeout(() => {
            console.log('⏱️ Inactivité détectée, fin de l\'activité');
            endActivity();
        }, 30000); // 30 secondes
    }
    
    // Réinitialiser le timer à chaque interaction
    ['click', 'keypress', 'touchstart', 'mousemove'].forEach(event => {
        document.addEventListener(event, resetInactivityTimer, { passive: true });
    });
    
    resetInactivityTimer();
    
})();