-BİLGİ YÖNETİM SİSTEMİ(INFORMATİON MANAGEMENT SYSTEM)-

->Flask tabanlı öğrenci bilgi sistemi uygulaması(web). Bu uygulama ile öğrenci kayıtlarını ekleyebilir, güncelleyebilir, silebilir,arayabilir
   ve öğrencilere not ekleyebilirsiniz.

->Projede Bulunan Özellikler:
   Öğrenci listeleme.İsterseniz json formatında görüntüleyebilirsiniz.
   Yeni öğrenci ekleme
   Öğrenci silme (silinen öğrencileri deleteStudent adlı tabloda tutacağız.)
   Öğrenci bilgilerini görüntüleme
   Öğrenci bilgilerini güncelleme
   Öğrenciyi okul numarası ile arama
   Öğrencilere not ekleme

->öğrenci güncellemek için tarayıcıya şunu yazın:
   http://127.0.0.1:5000/studentUpdate/güncellenecek öğrenci id'si

   example:
   id'si 34 olan bir öğrenciyi güncellemek için tarayıcıya şunu yazmalısınız.
   http://127.0.0.1:5000/studentUpdate/34


->öğrencileri json formatında görüntülemek istiyorsanız tarayıcıya şunu yazın:
   http://127.0.0.1:5000/student?format=json



->sadece bir öğrencinin bilgilerini görmek istiyorsanız tarayıcıya şunu yazın:
http://127.0.0.1:5000/studentInfo/öğrenci id'si

example:
   id'si 34 olan öğrencinin bilgilerini görmek için tarayıcıya şunu yazmalısınız:
   http://127.0.0.1:5000/studentInfo/34

   

->Hangi Diller veya frameworkleri kullandım;

   Back-end:Python,Flask
   front-end:Html,Css
   Veritabanı: MySql

+ekstra olarak mysql-connector kütüphanesinin Error sınıfını ve dekoratör kullandık.

->Proje Yapımız nasıl?

student-management-system/
   app.py                 #Ana app'imiz
   templates/             #HTML şablonları
      index.html
      students.html
      addStudent.html
      deleteStudent.html
      studentInfo.html
      studentUpdate.html
      studentSearch.html
      addGrade.html
   .env
   README.md

->app.py'yle aynı dizinde bir .env dosyası oluşturun:
   DB_HOST=127.0.0.1
   DB_USER=root
   DB_PASSWORD=şifreniz
   DB_NAME=veritabanı ismi
   SECRET_KEY=gizli anahtarınız


->İletişim;
   firatoz412@gmail.com
   
