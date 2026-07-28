import os
from django.core.management.base import BaseCommand
from apps.airline_ticketing.models import Hotel

class Command(BaseCommand):
    help = "Seed Makkah and Madinah Hotels from official records"

    def handle(self, *args, **options):
        makkah_hotels = [
            ("ARAFAT ZAHBI", "UMM AL-MOUMIN STREET KUDAI", "SHUTTLE SERVICE"),
            ("FAKHIR AL AZIZIA", "AZIZIA MAKKAH", "SHUTTLE SERVICE"),
            ("TAJ FIDDI HOTEL", "AJYAD STREET", "700-800 MTR"),
            ("QILA AJYAD", "AJYAD STREET", "SHUTTLE SERVICE"),
            ("THAT HOTEL", "MISFALAH KUBRI", "800-900 MTR"),
            ("AK KISWAH TOWERS", "AL TAYSIR STREET", "SHUTTLE SERVICE"),
            ("MIAAD AL MAJD", "AL HAJLAH ROAD", "700-800 MTR"),
            ("LAND PREMIUM", "AL HAJLAH ROAD", "1000 MTR"),
            ("RUKAN AL ZAWIA", "IBRAHIM KHALIL ROAD", "700-800 MTR"),
            ("MELLA 1 / MELLA 2", "IBRAHIM KHALIL ROAD", "650-700 MTR"),
            ("DIWAN AL BAIT", "IBRAHIM KHALIL ROAD", "500-600 MTR"),
            ("SAIF AL MAJD", "AL HAJLAH ROAD", "650 MTR"),
            ("AREEJ AL ZAHBI", "AL HAJLAH ROAD", "450-500 MTR"),
            ("ARFAT GOLDEN RUSHD (old DAR AL KHALIL AL RUSHD)", "IBRAHIM KHALIL ROAD", "500 MTR"),
            ("SHAMS AL ZAHBI", "AL HIJRAH ROAD", "350-400 MTR"),
            ("DAIF AJYAD", "AJYAD STREET", "250-300 MTR"),
            ("ZIAFA MUBARAK", "IBRAHIM KHALIL ROAD", "200 MTR"),
            ("LOLO AL FALAH", "IBRAHIM KHALIL ROAD", "200 MTR"),
            ("WEDAM SIX", "IBRAHIM KHALIL ROAD", "SHUTTLE"),
            ("WHITE LION", "HIJRA ROAD", "1200 MTR"),
            ("MASRAT KHALIL / NADA HIJRA", "IBRAHIM KHALIL ROAD", "750 MTR"),
            ("MASRAT GOLDEN", "IBRAHIM KHALIL ROAD", "600 MTR"),
            ("QASAR E SAAD", "IBRAHIM KHALIL ROAD", "1400 M"),
            ("DYAR MATAR", "IBRAHIM KHALIL ROAD", "1200 MTR"),
            ("JADA KHALIL", "IBRAHIM KHALIL ROAD", "1200 MTR"),
            ("FUNDAQ BILAL", "SHUTTLE SERVICE", "1500 M"),
            ("KISWA TOWER", "IBRAHIM KHALIL ROAD", "1300 M"),
            ("TARA JAWART", "SHUTTLE SERVICE", "1800 M"),
            ("TARA JAWART & MULTIQA", "HJRA MISFLAH", "750-800 M"),
            ("HOTEL ONE", "NEAR MISFALLAH QUBRI", "1100 M"),
            ("NAJMA KHALLEEL", "HIJRA ROAD", "700 M"),
            ("SAIF AL MAJD", "HIJRA ROAD", "600-650 M"),
            ("VOCU MAKKAH", "IBRAHIM KHALIL ROAD", "1200 MTR"),
            ("EMAR AL KHAIR AL MASSI", "HIJRA ROAD", "700 M"),
            ("BADAR MASA", "IBRAHIM KHALIL ROAD", "600 MTR"),
            ("HOTEL NUMBER ONE 3", "IBRAHIM KHALIL ROAD", "SHUTTLE"),
            ("NAZEEL AL MASHAER / LAND PREMIUM OR SIMILAR", "HIJRA ROAD", "1100 M"),
            ("FUNDAQ HARIS", "INSIDE KUBRI IBRAHIM KHALIL ROAD", "800 M"),
            ("ZAD AL BAIT", "IBRAHIM KHALIL ROAD", "750 MTR"),
            ("MAKARAM AL HIJRA (Ex Burj Abbas)", "HIJRA ROAD", "650 MTR"),
            ("MIRA SHAEB", "HARAM FACING (FRONT ROW GHAZA SIDE)", "450 M"),
            ("MATHAR AL JIWAR / BADAR MASSA OR SIMILAR", "HIJRA ROAD", "550 M"),
            ("AJWAZIAFA / AIMILAR", "AZIZA", "SHUTTLE SERVICE"),
            ("LOLO TOUHEED", "IBRAHIM KHALIL ROAD MISFALLAH", "1200 MTR"),
            ("MULTIQA IBADAT & TARA JAWART", "HIJRA ROAD", "900 M"),
            ("JAFRIA (MASAR AL AEZ 2)", "HIJRA ROAD", "750-800 M"),
            ("JAWRAT BAIT (ARAFAT ZEHBI)", "IBRAHIM KHALIL ROAD", "550-600 M"),
            ("SWISS KHALIL / BLORA MOAZAN", "MAIN IBRAHIM KHALIL ROAD", "600 MTR"),
            ("EMAR ANDALUSIA", "MAIN IBRAHIM KHALIL ROAD", "350-400 MTR"),
            ("HIBA HIJRA 6", "IBRAHIM KHALIL ROAD", "SHUTTLE"),
            ("FUNDAQ HARIS OR SIMILAR", "INSIDE KUBRI IBRAHIM KHALIL ROAD", "750 M"),
            ("ZAD AL BAIT OR SIMILAR", "IBRAHIM KHALIL ROAD", "750 M"),
            ("MUKAREM HIJRA", "HIJRA ROAD", "850 M"),
            ("MIRA SHA OR SIMILAR", "GAZA SIDE", "450 M"),
            ("SAFWA AL MAID", "IBRAHIM KHALIL", "SHUTTLE"),
            ("AL AREEQ", "IBRAHIM KHALIL", "600 M"),
            ("EMAR AL KHAIR", "HIJRA ROAD", "700 M"),
            ("MINAR AL EMAN", "HIJRA ROAD", "550 M"),
        ]

        madinah_hotels = [
            ("HALA TAIBAR", "ABDUL AZIZ ROAD", "SHUTTLE SERVICE"),
            ("MANAZIL MARJAN", "QURAN NAZIL ROAD", "SHUTTLE SERVICE"),
            ("DIYAR AL SAFA", "MASJID BILAL SIDE", "700-750 MTR"),
            ("WAHAT AL SHARK", "MASJID BILAL SIDE", "700-750 MTR"),
            ("NAZAL ESSA KARIM", "ALBAIK OPPOSITE SIDE", "600 MTR"),
            ("ANWAR AL MADAIN", "ALBAIK OPPOSITE SIDE", "650-700 MTR"),
            ("MANAZIL MAJD", "ALBAIK OPPOSITE SIDE", "650-700 MTR"),
            ("MAJD SILVER", "MASJID BILAL SIDE", "400-500 MTR"),
            ("BURJ MUKHTARA", "BAB AL SALAM ROAD", "300-350 MTR"),
            ("BIR AL EIMAN", "SOUTH MARKAZIA", "200-250 MTR"),
            ("SIDRA MADINAH", "SOUTH MARKAZIA", "200-250 MTR"),
            ("TAIF NEBRAS", "SOUTH MARKAZIA", "200-250 MTR"),
            ("WAHA NAZEEL", "MARKAZIA GARBIA SIDE", "100 MTR"),
            ("QADAT AL DYAFAH", "OMER BIN AL KHATTAB ROAD", "SHUTTLE SERVICE"),
            ("HAMOUDA AL MASI", "MASJID BILAL SIDE", "650 MTR"),
            ("HAMOUDA NEBRAS SILVER", "AL ZAHIDA AREA QUBA ROAD", "550 MTR"),
            ("HAMOUDA NEBRAS 1&2", "MASJID BILAL SIDE", "450 MTR"),
            ("REHAB AL MADAIN", "QURBAN ROAD", "1000 MTR"),
            ("ALIA DAOUDIA HOTEL 2", "QURBAN ROAD", "900 MTR"),
            ("SHAZA MUNAWARA", "NEAR TOP 10", "700 MTR"),
            ("MAHAD AL MADINA", "AWALI SIDE", "700 MTR"),
            ("ZAHRA TABIA 3", "MASJID BILAL SIDE", "500 MTR"),
            ("ELAF QUBA HOTEL", "QUBA ROAD IN FRONT MARKAZIA", "450 MTR"),
            ("ARJAWAN AL MADINA", "MARKAZIA", "250 MTR"),
            ("MARKAZIA / SIMILAR", "MARKAZIA", "100 MTR"),
            ("RETAJ AL MADINA", "AWALI SIDE", "1200 M + SHUTTLE"),
            ("SHAZA HIJRA", "SHAHRAH SALAM SIDE", "850 MTR"),
            ("SHAZA AMAN", "SHAHRAH SALAM SIDE", "750 MTR"),
            ("SHAZA MUNAWARA", "KING FAHAD ROAD", "750-800 MTR"),
            ("MAHAD AL MADINA 2", "NEAR BILAL MASJID", "450-500 MTR"),
            ("DIYAR AL AWS", "ENTERANCE OF QUBA STREET", "400 MTR"),
            ("SHAZA ZAFRANI", "SHAHRAH SALAM SIDE", "350 MTR"),
            ("ARJAWAN AL MADINA OR SIMILAR", "MARKAZIA", "300 MTR"),
            ("KINAN MADINA", "MIAN QURBAN ROAD", "900 MTR"),
            ("DAR AJYAL 1", "SHUMALIA LADIES GATE SIDE", "750 MTR"),
            ("ABDULLAH FOUZAN", "MASJID BILAL SIDE", "600 MTR"),
            ("KARAM GOLDEN", "MASJID BILAL SIDE", "550 MTR"),
            ("ANSAR PLUS", "MASJID BILAL SIDE", "500 MTR"),
            ("WIDYAR AL MADINA / ROU KHAIR", "BAB AL SALAM ROAD", "350 MTR"),
            ("ROU TAIBA", "MARKAZIA", "100 MTR"),
            ("MARKAZIA / SIMILAR", "ANY HOTEL IN MARKZAIA", "100-250 MTR"),
            ("NOVOTEL", "GHARBIA SIDE", "100-150 MTR"),
            ("TAJ AL MADINA OR SIMILAR", "AWALI SIDE", "1200 MTR SHUTTLE"),
            ("ABRAJ TAIBA SILIVER OR SIMILAR", "MARKAZIA", "300 MTR"),
            ("NUZUL WAHA MADAIN", "MASJID BILAL SIDE", "500 MTR"),
            ("ERGWAN AL MADINAH", "SOUTH MARKAZIA", "250 MTR"),
            ("MARJAN GOLDEN", "GARBIA SIDE", "100 MTR"),
            ("NAJMA QUBA", "QUBA ROAD", "450 M"),
        ]

        count_m = 0
        for name, loc, dist in makkah_hotels:
            Hotel.objects.get_or_create(
                name=name,
                city='makkah',
                defaults={
                    'location': loc,
                    'distance_from_haram': dist,
                    'is_active': True
                }
            )
            count_m += 1

        count_mad = 0
        for name, loc, dist in madinah_hotels:
            Hotel.objects.get_or_create(
                name=name,
                city='madinah',
                defaults={
                    'location': loc,
                    'distance_from_haram': dist,
                    'is_active': True
                }
            )
            count_mad += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count_m} Makkah hotels and {count_mad} Madinah hotels!"))
