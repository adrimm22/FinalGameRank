import xml.etree.ElementTree as ET
import requests
from django.core.management.base import BaseCommand
from gamerank.models import Game  # Importamos el modelo en inglés


class Command(BaseCommand):
    help = "Imports games from listado1.xml (LIS1- prefix)"

    def handle(self, *args, **kwargs):
        try:
            # URL del XML
            url = "https://gitlab.eif.urjc.es/cursosweb/2024-2025/final-gamerank/-/raw/main/listado1.xml"

            self.stdout.write(self.style.WARNING(f'Downloading XML from {url}...'))

            response = requests.get(url)
            response.raise_for_status()

            # Parseamos el contenido
            root = ET.fromstring(response.content)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading XML file: {e}"))
            return

        count = 0
        # Iteramos sobre los elementos (usando las etiquetas de tu código)
        for game_elem in root.findall('game'):
            # Generamos el ID con el prefijo
            xml_id = game_elem.find('id').text.strip() if game_elem.find('id') is not None else str(count)
            game_id = "LIS1-" + xml_id

            # Creamos o actualizamos el objeto Game
            # Usamos los nombres de campos en inglés definidos en models.py
            game, created = Game.objects.get_or_create(
                game_id=game_id,
                defaults={
                    'title': game_elem.findtext('title', '').strip(),
                    'platform': game_elem.findtext('platform', '').strip(),
                    'genre': game_elem.findtext('genre', '').strip(),
                    'developer': game_elem.findtext('developer', '').strip(),
                    'publisher': game_elem.findtext('publisher', '').strip(),
                    'short_description': game_elem.findtext('short_description', '').strip(),
                    'thumbnail': game_elem.findtext('thumbnail', '').strip(),
                    'game_url': game_elem.findtext('game_url', '').strip(),
                    # 'profile_url': Si tu modelo Game no tiene este campo, borra esta línea.
                    # Por defecto en nuestros pasos anteriores no lo pusimos, así que lo omito para evitar errores.
                }
            )

            # Gestión de la fecha
            date_str = game_elem.findtext('release_date', '').strip()
            if date_str:
                try:
                    game.release_date = date_str  # Expected format: 'YYYY-MM-DD'
                    game.save()
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Invalid date for {game_id}: {e}"))

            status = "Created" if created else "Already existed"
            self.stdout.write(f"- {status}: {game.title}")
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Process finished! Total games processed: {count}'))