import unittest

from prospeccao.filtros import filtrar_sem_site, normalizar_lugar


class TestNormalizarLugar(unittest.TestCase):
    def test_empresa_sem_site(self):
        lugar = {
            "displayName": {"text": "Padaria Bela Vista"},
            "formattedAddress": "Rua X, 123, Osasco - SP",
        }
        empresa = normalizar_lugar(lugar)
        self.assertEqual(empresa.nome, "Padaria Bela Vista")
        self.assertFalse(empresa.tem_site)
        self.assertIsNone(empresa.site)

    def test_empresa_com_site(self):
        lugar = {
            "displayName": {"text": "Clínica Sorriso"},
            "websiteUri": "https://clinicasorriso.com.br",
        }
        empresa = normalizar_lugar(lugar)
        self.assertTrue(empresa.tem_site)
        self.assertEqual(empresa.site, "https://clinicasorriso.com.br")

    def test_telefone_usa_fallback_internacional(self):
        lugar = {
            "displayName": {"text": "Oficina do Zé"},
            "internationalPhoneNumber": "+55 11 91234-5678",
        }
        empresa = normalizar_lugar(lugar)
        self.assertEqual(empresa.telefone, "+55 11 91234-5678")


class TestFiltrarSemSite(unittest.TestCase):
    def test_filtra_apenas_sem_site(self):
        sem_site = normalizar_lugar({"displayName": {"text": "A"}})
        com_site = normalizar_lugar({"displayName": {"text": "B"}, "websiteUri": "https://b.com"})
        resultado = filtrar_sem_site([sem_site, com_site])
        self.assertEqual(resultado, [sem_site])

    def test_lista_vazia(self):
        self.assertEqual(filtrar_sem_site([]), [])


if __name__ == "__main__":
    unittest.main()
