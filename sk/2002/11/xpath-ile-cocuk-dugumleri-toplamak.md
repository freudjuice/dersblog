# XPath İle Çocuk Düğümleri Toplamak


XPath İle Çocuk Düğümleri Toplamak



 Farzedelim ki, aşağıda örneği gösterilen dosya içinden eCRM baslığı taşıyan etiketlerin altındaki bütün çocuk düğümleri toplamak istiyoruz.              <?xml version="1.0" encoding="iso-8859-9"?><kategoriler><kategori baslik="eCRM"> <yazi>a_etl.xml<tarih>19 Nisan 2002</tarih></yazi> <yazi>a_hangi_verileri_alalim.xml<tarih>19 Nisan 2002</tarih></yazi> <yazi>a_internet_veri_ambari.xml<tarih>19 Nisan 2002</tarih></yazi> <yazi>a_musteri_kayitlari.xml<tarih>19 Nisan 2002</tarih></yazi> <yazi>a_oracle_kavramlari.xml<tarih>19 Nisan 2002</tarih></yazi> <yazi>a_oracle_kullanim.xml<tarih>19 Nisan 2002</tarih></yazi> <yazi>a_oracle_parallel.xml<tarih>19 Nisan 2002</tarih></yazi> <yazi>a_oracle_query_optimize.xml<tarih>19 Nisan 2002</tarih></yazi> <yazi>a_veri_madenciligi.xml<tarih>19 Nisan 2002</tarih></yazi></kategori><kategori baslik="Genel"> <yazi>a_acik_anahtar_sifreleme.xml<tarih>19 Nisan 2002</tarih></yazi> <yazi>a_continous_integration.xml<tarih>19 Nisan 2002</tarih></yazi> <yazi>a_cvs.xml<tarih>19 Nisan 2002</tarih></yazi></kategori></kategoriler>             Bunun için şöyle bir XPath komutu vermemiz gerekecek.               /kategoriler/kategori[@baslik='"eCRM"']/yazi              Bu komut kategoriler, kategori altına gidip, eCRM baslığı taşıyan bütün yazı etiketlerinin değerlerini getirecektir. Java ile şöyle kodlama yapabiliriz.                  public ArrayList kategoriAltindakiYazilar(String kategori){ Document doc = belgeOku(); String xpath = "/kategoriler/kategori[@baslik='" + kategori + "']/yazi"; NodeList liste = null; ArrayList sonListe = new ArrayList(); try {   liste = org.apache.xpath.XPathAPI.selectNodeList(doc, xpath); } catch (javax.xml.transform.TransformerException e) { } for (int i=0; i < liste.getLength(); i++) {   Element elem = (Element)liste.item(i);   sonListe.add(elem.getFirstChild().getNodeValue()); } return sonListe;}              getFirstChild (ilk çocuğu getir) çağrısına dikkatinizi çekmek istiyorum. Bu çağrı ile, zaten başka çocuğu olmayan yazı etiketinin alt değerini almış oluyoruz. Tabii getNodeValue (dügüm değerini getir) dememiz de gerekti. Anlamamız gereken nokta, 'yazı' altında bulunan değerin etiketin kendisinde değil, alt düğüm olarak başka bir düğümde durmasıdır.                Hemen JUnit testimizi yazalım:                  public void testYaziListe() throws Exception { ArticleList liste = new ArticleList(); ArrayList l = liste.kategoriAltindakiYazilar("eCRM"); assertTrue(l.size() > 0);}



