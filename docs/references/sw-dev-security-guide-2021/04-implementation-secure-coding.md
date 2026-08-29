---
type: Guide
title: 소프트웨어 개발보안 가이드(2021) 제4장 — 구현단계 시큐어코딩 가이드
description: 구현단계 보안약점 제거 기준 49개 항목의 개요·보안대책과 JAVA/C/C#/Android 코드예제(안전하지 않은 코드 ↔ 안전한 코드). 원문 136~340쪽의 마크다운 변환본.
resource: 소프트웨어 개발보안 가이드(2021)
status: stable
tags: [개발보안, 시큐어코딩, 행정안전부, kisa, 보안약점, 구현단계, 코드예제]
generated: { by: "claude-code/claude-opus-5", at: "2026-08-29T00:00:00Z" }
sources:
  - { id: pdf, resource: "소프트웨어_개발보안_가이드(2021)_수정배포.pdf — 원본 PDF (저장소 미포함)", title: "전자정부 SW 개발·운영자를 위한 소프트웨어 개발보안 가이드", author: "행정안전부·한국인터넷진흥원", last_modified: "2021-11-30" }
---

> **문서명**: 전자정부 SW 개발·운영자를 위한 소프트웨어 개발보안 가이드 | **발행**: 행정안전부·한국인터넷진흥원 | **발행일**: 2021.11.
> 원본: 소프트웨어_개발보안_가이드(2021)_수정배포.pdf — 본 문서는 PDF 원문을 마크다운으로 변환한 참고자료입니다. 전체 구성은 [index.md](index.md)를 참고한다.

# 제4장 구현단계 시큐어코딩 가이드

- 제1절 입력데이터 검증 및 표현
- 제2절 보안기능
- 제3절 시간 및 상태
- 제4절 에러처리
- 제5절 코드오류
- 제6절 캡슐화
- 제7절 API 오용

## 제1절 입력데이터 검증 및 표현

프로그램 입력값에 대한 검증 누락 또는 부적절한 검증, 데이터의 잘못된 형식지정, 일관되지 않은 언어셋 사용 등으로 인해 발생되는 보안약점으로 SQL 삽입, 크로스사이트 스크립트(XSS) 등의 공격을 유발할 수 있다.

### 1. SQL 삽입

#### 가. 개요

데이터베이스(DB)와 연동된 웹 응용프로그램에서 입력된 데이터에 대한 유효성 검증을 하지 않을 경우, 공격자가 입력 폼 및 URL 입력란에 SQL 문을 삽입하여 DB로부터 정보를 열람하거나 조작할 수 있는 보안약점을 말한다.

취약한 웹 응용프로그램에서는 사용자로부터 입력된 값을 필터링 과정 없이 넘겨받아 동적 쿼리 (Dynamic Query)4를 생성하기 때문에 개발자가 의도하지 않은 쿼리가 생성되어 정보유출에 악용될 수 있다.

> <sup>4</sup> 동적쿼리(Dynamic Query) : DB에서 실시간으로 받는 쿼리. Parameterized Statement가 동적 쿼리가 됨

#### 나. 보안대책

PreparedStatement5객체 등을 이용하여 DB에 컴파일 된 쿼리문(상수)을 전달하는 방법을 사용한다. PreparedStatement를 사용하는 경우에는 DB 쿼리에 사용되는 외부 입력값에 대하여 특수문자 및 쿼리 예약어를 필터링하고, 스트러츠(Struts), 스프링(Spring) 등과 같은 프레임워크를 사용하는 경우에는 외부 입력값 검증모듈 및 보안모듈을 상황에 맞추어 적절하게 사용한다.

#### 다. 코드예제

다음은 안전하지 않은 코드의 예로, 외부로부터 입력받은 gubun의 값을 아무런 검증과정을 거치지 않고 SQL 쿼리를 생성하는데 사용하고 있다. 이 경우 gubun의 값으로 a' or 'a' = 'a 를 입력하면 조건절이 b_gubun = 'a' or 'a' = 'a' 로 바뀌어 쿼리의 구조가 변경되어 board 테이블의 모든 내용이 조회된다.

**안전하지 않은 코드의 예 JDBC API**

```java
//외부로부터 입력받은 값을 검증 없이 사용할 경우 안전하지 않다.
String gubun = request.getParameter("gubun");
......
String sql = "SELECT * FROM board WHERE b_gubun = '" + gubun + "'";
Connection con = db.getConnection();
Statement stmt = con.createStatement();
//외부로부터 입력받은 값이 검증 또는 처리 없이 쿼리로 수행되어 안전하지 않다.
ResultSet rs = stmt.executeQuery(sql);
```

> <sup>5</sup> PreparedStatement : 컴파일된 쿼리 객체로 MySQL, Oracle, DB2, SQL Server 등에서 지원하며, Java의 JDBC, Perl의 DBI, PHP의 PDO, ASP의 ADO를 이용하여 사용가능

이를 안전한 코드로 변환하면 다음과 같다. 파라미터(Parameter)를 받는 PreparedStatement 객체를 상수 스트링으로 생성하고, 파라미터 부분을 setString, setParameter 등의 메소드로 설정 하여, 외부의 입력이 쿼리문의 구조를 바꾸는 것을 방지해야 한다.

**안전한 코드의 예 JDBC API**

```java
String gubun = request.getParameter("gubun");
......
//1. 사용자에 의해 외부로부터 입력받은 값은 안전하지 않을 수 있으므로, PreparedStatement
         사용을 위해 ?문자로 바인딩 변수를 사용한다.
String sql = "SELECT * FROM board WHERE b_gubun = ?";
Connection con = db.getConnection();
//2. PreparedStatement 사용한다.
PreparedStatement pstmt = con.prepareStatement(sql);
//3. PreparedStatement 객체를 상수 스트링으로 생성하고, 파라미터 부분을 setString 등의
    메소드로 설정하여 안전하다.
pstmt.setString(1, gubun);
ResultSet rs = pstmt.executeQuery();
```

MyBatis Data Map은 외부에서 입력되는 값이 SQL 질의문을 연결하는 문자열로 사용되는 경우에 의도하지 않은 정보가 노출될 수 있는 공격 형태이다.

**안전하지 않은 코드의 예 MyBatis**

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN“
   "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
......
<select id="boardSearch" parameterType="map" resultType="BoardDto">
//$기호를 사용하는 경우 외부에서 입력된 keyword값을 문자열에 결합한 형태로 쿼리에 반영되므로
  안전하지 않다.
  select * from tbl_board where title like '%$ {keyword }%' order by pos asc
</select>
```

외부 입력값을 MyBatis 쿼리맵에 바인딩할 경우 $ 기호가 아닌 # 기호를 사용해야 한다. $ 기호를 사용하는 경우 입력값을 문자열에 결합하는 형태로 쿼리에 반영하므로 쿼리문이 조작될 수 있다.

**안전한 코드의 예 MyBatis**

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
   "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
......
<select id="boardSearch" parameterType="map" resultType="BoardDto">
//$ 대신 #기호를 사용하여 변수가 쿼리맵에 바인딩 될 수 있도록 수정하는 것이 안전하다.
  select * from tbl_board where title like '%'||# {keyword }||'%' order by pos asc
</select>
```

Hibernate의 경우 기본으로 PreparedStatement를 사용하지만, 아래 코드와 같이 파라미터 바인딩(binding)없이 사용할 경우 외부로부터 입력받은 값에 의해 쿼리의 구조가 변경 될 수 있다.

**안전하지 않은 코드의 예 Hibernate**

```java
import org.hibernate.Query
import org.hibernate.Session
......
//외부로부터 입력받은 값을 검증 없이 사용할 경우 안전하지 않다.
String name = request.getParameter("name");
//Hiberate는 기본으로 PreparedStatement를 사용하지만, 파라미터 바인딩 없이 사용 할 경우
 안전하지 않다.
Query query = session.createQuery("from Student where studentName = '" + name + "' ");
```

아래 코드와 같이 외부 입력값이 위치하는 부분을 ? 또는 :명명된 파라미터 변수로 설정하고, 실행 시에 해당 파라미터가 전달되는 바인딩(binding)을 함으로써 외부의 입력이 쿼리의 구조를 변경시키는 것을 방지할 수 있다.

**안전한 코드의 예 Hibernate**

```java
import org.hibernate.Query
import org.hibernate.Session
......
String name = request.getParameter("name");
//1. 파라미터 바인딩을 위해 ?를 사용한다.
Query query = session.createQuery("from Student where studentName = ? ");
//2. 파라미터 바인딩을 사용하여 외부 입력값에 의해 쿼리 구조 변경을 못하게 사용하였다.
query.setString(0, name);
import org.hibernate.Query
import org.hibernate.Session
......
String name = request.getParameter("name");
//1. 파라미터 바인딩을 위해 명명된 파라미터 변수를 사용한다.
Query query = session.createQuery("from Student where studentName = :name ");
//2. 파라미터 바인딩을 사용하여 외부 입력값에 의해 쿼리 구조 변경을 못하게 사용하였다.
query.setParameter("name", name);
```

다음 C# 코드는 외부 입력값을 SQL 쿼리에 직접 사용하고 있어, 쿼리의 구조가 변경될 위험이 있습니다.

**안전하지 않은 코드의 예 C#**

```csharp
public void ButtonClickBad(object sender, EventArgs e)
{
  string connect = "MyConnString";
  string usrinput = Request["ID"];
// 외부로부터 입력받은 값을 SQL 쿼리에 직접 사용하는 것은 안전하지 않다.
  string query = "Select * From Products Where ProductID = " + usrinput;
  using (var conn = new SqlConnection(connect))
{

                                 안전하지 않은 코드의 예 C#

        using (var cmd = new SqlCommand(query, conn))
{
            conn.Open();
            cmd.ExecuteReader(); /* BUG */
        }
    }
}
```

파라미터 바인딩을 사용하여 쿼리의 구조가 변경될 위험을 제거해야 합니다.

**안전한 코드의 예 C#**

```csharp
void ButtonClickGood(object sender, EventArgs e)
 {
  string connect = "MyConnString";
      string usrinput = Request["ID"];
     //파라미터 바인딩을 위해 @ 을 사용합니다. 외부입력 값에 의해 쿼리 구조 변경을 할 수 없습니다.
  string query = "Select * From Products Where ProductID = @ProductID";
  using (var conn = new SqlConnection(connect))
  {
    using (var cmd = new SqlCommand(query, conn))
    {
      cmd.Parameters.AddWithValue("@ProductID",
      Convert.ToInt32(Request["ProductID"]);
      conn.Open();
      cmd.ExecuteReader();
    }
  }
```

#### 라. 참고자료

- ① CWE-89 SQL Injection, MITRE, http://cwe.mitre.org/data/definitions/89.html
- ② Threat and Vulnerability, "SQL Injection", Microsoft, http://technet.microsoft.com/en-us/library/ms161953%28v=SQL.105%29.aspx
- ③ Input validation and Data Sanitization, Threat and Vulnerability, Prevent SQL Injection, CERT, http://www.securecoding.cert.org/confluence/display/java/IDS00-J.+Prevent+SQL+injection
- ④ SQL Injection Prevention Cheat Sheet, OWASP https://www.owasp.org/index.php/SQL_Injection_Prevention_Cheat_Sheet
### 2. 코드삽입

#### 가. 개요

공격자가 소프트웨어의 의도된 동작을 변경하도록 임의 코드를 삽입하여 소프트웨어가 비정상적으로 동작하도록 하는 보안약점을 말한다. 코드 삽입은 프로그래밍 언어 자체의 기능에 의해서만 제한된다는 점에서 운영체제 명령어 삽입과 다르다.

취약한 프로그램에서 사용자의 입력 값에 코드가 포함되는 것을 허용할 경우, 공격자는 개발자가 의도하지 않은 코드를 실행하여 권한을 탈취하거나 인증 우회, 시스템 명령어 실행 등을 할 수 있다.

#### 나. 보안대책

동적코드를 실행할 수 있는 함수를 사용하지 않는다. 필요 시, 실행 가능한 동적코드를 입력 값으로 받지 않도록, 외부 입력 값에 대하여 화이트리스트 방식으로 구현한다. 또는 유효한 문자만 포함하도록 동적 코드에 사용되는 사용자 입력 값을 필터링 한다.

#### 다. 코드예제

다음 예제의 소스코드는 javax.script.ScriptEngineManager을 사용하여 ScriptEnigneManeger()로 사용자의 입력을 실행하여 출력한다. 이 경우, 공격자는 조작된 인수를 입력한 공격코드를 이용하여 새로운 파일을 만들거나 덮어씌울 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
public class CodeInjectionController {
@RequestMapping(value = "/execute", method = RequestMethod.GET)
       public String execute(@RequestParam("src") String src)
       throws ScriptException {
               ScriptEngineManager scriptEngineManager = new
               ScriptEngineManager();
               ScriptEngine scriptEngine =
               scriptEngineManager.getEngineByName("javascript");
               // 외부 입력값인 src를 javascript eval 함수로 실행하고 있어 안전하지 않다.
               String retValue = (String)scriptEngine.eval(src);
               return retValue;
       }
}
```

다음 예제는 외부 입력 값을 javascript의 new Function()으로 동적으로 코드를 실행할 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
<body>
<%
String name = request.getparameter("name");
    %>
    ...
<script>
    // 외부 입력값인 name을 javascript new Function()을 이용하여 문자열을 함수로 실행하고 있다.
           (new Function(<%=name%>))();
</script>
</body>
```

외부 입력 값에 실행이 가능한 코드가 포함되어 있을 경우 입력 값을 필터링 하여 사전에 검증하는 코드를 추가하면 코드삽입을 완화할 수 있다. 이런 조치를 취할 경우 입력 값의 형태에 따라 정규 표현식을 변형하여 적용해야 한다.

**안전한 코드의 예 JAVA**

```java
@RequestMapping(value = "/execute", method = RequestMethod.GET)
public String execute(@RequestParam("src") String src) throws ScriptException {
              // 정규식을 이용하여 특수문자 입력시 예외를 발생시킨다.
              if (src.matches("[ \ \w]*") == false) {
                        throw new IllegalArgumentException();
              }
               ScriptEngineManager scriptEngineManager = new ScriptEngineManager();
          ScriptEngine scriptEngine = scriptEngineManager.getEngineByName("javascript");
              String retValue = (String)scriptEngine.eval(src);
              return retValue;
}
```

스크립트 실행이 필요한 경우는 화이트리스트 방식을 적용하여 유효한 문자인 경우에만 실행되도록 하고 그 외의 경우는 모두 예외 처리한다.

**안전한 코드의 예 JAVA**

```java
@RequestMapping(value = "/execute", method = RequestMethod.GET)
public String execute(@RequestParam("src") String src) throws ScriptException {
        // 유효한 문자 “_” 일 경우 실행할 메소드 호출한다.
        if (src.matches("UNDER_BAR“) == true) {
              ...
              // 유효한 문자 “$” 일 경우 실행할 메소드 호출한다.
              } else if (src.matches("DOLLAR“) == true) {
              ...
               // 유효하지 않은 특수문자 입력시 예외를 발생시킨다.
              } else {
                     throw new IllegalArgumentException();
              }
       ...

}
```

#### 라. 참고자료

- ① CWE-94: Improper Control of Generation of Code (‘Code Injection’) , MITRE, http://cwe.mitre.org/data/definitions/94.html
- ② CWE-95: Improper Neutralization of Directives in Dynamically Evaluated Code ('Eval Injection') , MITRE, http://cwe.mitre.org/data/definitions/95.html
- ③ Code Injection Software Attack, OWASP, https://owasp.org/www-community/attacks/Code_Injection
### 3. 경로 조작 및 자원 삽입

#### 가. 개요

검증되지 않은 외부 입력값으로 파일 및 서버 등 시스템 자원에 대한 접근 혹은 식별을 허용할 경우, 입력값 조작으로 시스템이 보호하는 자원에 임의로 접근할 수 있는 보안약점이다. 경로조작 및 자원삽입 약점을 이용하여 공격자는 자원의 수정․삭제, 시스템 정보누출, 시스템 자원 간 충돌로 인한 서비스 장애 등을 유발시킬 수 있다.

즉, 경로 조작 및 자원 삽입으로 공격자가 허용되지 않은 권한을 획득하여, 설정에 관계된 파일을 변경하거나 실행시킬 수 있다.

#### 나. 보안대책

외부의 입력을 자원(파일, 소켓의 포트 등)의 식별자로 사용하는 경우, 적절한 검증을 거치도록 하거나, 사전에 정의된 적합한 리스트에서 선택되도록 한다. 특히, 외부의 입력이 파일명인 경우에는 경로순회(directory traversal)3) 공격의 위험이 있는 문자( “ / ￦ .. 등 )를 제거할 수 있는 필터를 이용한다.

#### 다. 코드예제

외부 입력값(P)이 버퍼로 내용을 옮길 파일의 경로설정에 사용되고 있다. 만일 공격자에 의해 P의 값으로 ../../../rootFile.txt와 같은 값을 전달하면 의도하지 않았던 파일의 내용이 버퍼에 쓰여 시스템에 악영향을 준다.

**안전하지 않은 코드의 예 JAVA**

```java
 //외부로부터 입력받은 값을 검증 없이 사용할 경우 안전하지 않다.
  String fileName = request.getParameter("P");
  BufferedInputStream bis = null;
  BufferedOutputStream bos = null;
  FileInputStream fis = null;
  try {

                                안전하지 않은 코드의 예 JAVA

           response.setHeader("Content-Disposition", "attachment;filename="+fileName+";");
...
      //외부로부터 입력받은 값이 검증 또는 처리 없이 파일처리에 수행되었다.
      fis = new FileInputStream("C:/datas/" + fileName);
      bis = new BufferedInputStream(fis);
      bos = new BufferedOutputStream(response.getOutputStream());
```

외부 입력값에 대하여 상대경로를 설정할 수 없도록 경로순회 문자열( / ￦ & .. 등 )을 제거하고 파일의 경로설정에 사용한다.

**안전한 코드의 예 JAVA**

```java
String fileName = request.getParameter("P");
BufferedInputStream bis = null;
BufferedOutputStream bos = null;
FileInputStream fis = null;
try {
      response.setHeader("Content-Disposition", "attachment;filename="+fileName+";");
 ...
// 외부 입력받은 값을 경로순회 문자열(./￦)을 제거하고 사용해야한다.
      filename = filename.replaceAll("￦￦.", "").replaceAll("/", "").replaceAll("￦￦￦￦", "");
      fis = new FileInputStream("C:/datas/" + fileName);
      bis = new BufferedInputStream(fis);
      bos = new BufferedOutputStream(response.getOutputStream());
    int read;
while((read = bis.read(buffer, 0, 1024)) != -1) {
             bos.write(buffer,0,read);
      }
       }
```

인자값이 파일 이름인 경우에는 애플리케이션에서 정의(제한)한 디렉터리 c:￦help_files￦에서 파일을 읽어서 출력하지만, args[0]의 값으로 “..￦..￦..￦windows￦system32￦drivers￦etc ￦hosts”와 같이 경로조작 문자열을 포함한 입력이 들어오는 경우 접근이 제한된 경로의 파일을 열람할 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
public class ShowHelp {
   private final static String safeDir = "c:￦￦help_files￦￦";
   public static void main(String[] args) throws IOException {
        String helpFile = args[0];
        try (BufferedReader br = new BufferedReader(new FileReader(safeDir + helpFile))) {
            String line;
            while ((line = br.readLine()) != null) {
                  System.out.println(line);
            }
            ...
        }
```

외부 입력값으로 파일 경로를 조합하여 파일 시스템에 접근하는 경로를 만들지 말아야 한다. 외부에서 입력되는 값에 대하여 null 여부를 체크하고, 외부에서 입력되는 파일 이름에서 경로조작 문자열 제거 조치 후 사용하도록 한다.

**안전한 코드의 예 JAVA**

```java
public class ShowHelpSolution {
   private final static String safeDir = "c:￦￦help_files￦￦";
//경로조작 문자열 포함 여부를 확인하고 조치 후 사용하도록 한다.
  public static void main(String[] args) throws IOException {
    String helpFile = args[0];
    if (helpFile != null) {
          helpFile = helpFile.replaceAll("￦￦. {2, }[/￦￦￦￦]", "");
    }
try (BufferedReader br = new BufferedReader(new FileReader(safeDir + helpFile))) {
...
```

다음 C# 코드는 외부 입력값을 파일명에 바로 사용하고 있다. 이는 의도치 않은 파일의 손상을 가져올 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
//외부 입력 값이 검증 없이 파일처리에 사용 되었다.
string file = Request.QueryString["path"];
     if (file != null)
     {
             File.Delete(file); 6:
     }
```

외부 입력값에 경로 조작 문자열을 제거하여 조작 위험을 없앨 수 있다.

**안전한 코드의 예 C#**

```csharp
string file = Request.QueryString["path"];
  if (file != null)
{
//경로조작 문자열이 있는지 확인하고 파일 처리를 하도록 한다.
   if (file.IndexOf('￦￦') > -1 || file.IndexOf('/') > -1)
        {
             Response.Write("Path Traversal Attack");
        }
        else
        {
             File.Delete(file);
        }
    }
```

아래 C 코드는 외부 입력 값을 파일 경로로 바로 사용하고 있다. 이는 공격자가 환경 변수 reportfile을 조작하여 디렉토리 경로를 조작할 수 있다.

**안전하지 않은 코드의 예 C**

```c
char* filename = getenv(“reportfile”);
FILE *fin = NULL;
// 외부 설정 값에서 받은 파일 이름을 그대로 사용한다.
fin = fopen(filename, “r”);
while (fgets(buf, BUF_LEN, fin)) {
    // 파일 내용 출력
}
```

아래 C 코드는 외부에서 불러온 파일 이름을 그대로 사용하지 않고 경로 조작 가능성이 있는 문자열을 검증하고 사용한다.

**안전한 코드의 예 C#**

```csharp
FILE *fin = NULL;
 regex_t regex;
Int ret;
char* filename = getenv(“reportfile”);
ret = regcomp(&regex, “.*￦￦.￦￦..*”, 0);
// 경로 조작 가능성 있는 문자열 탐지
ret = regexec(&regex, filename, 0, NULL, 0);
If (!ret) {
    // 경로 조작 문자열 발견, 오류 처리
}
 // 필터링된 파일 이름으로 사용
fin = fopen(filename, “r”);
while (fgets(buf, BUF_LEN, fin)) {
 // 파일 내용 출력
}
```

#### 라. 참고자료

- ① CWE-99 Resource Injection, MITRE, http://cwe.mitre.org/data/definitions/99.html
- ② CWE-22 Path Traversal, MITRE, http://cwe.mitre.org/data/definitions/22.html
- ③ Path Traversal, OWASP, https://www.owasp.org/index.php/Path_Traversal
### 4. 크로스사이트 스크립트

#### 가. 개요

웹 페이지에 악의적인 스크립트를 포함시켜 사용자 측에서 실행되게 유도할 수 있다. 예를 들어, 검증되지 않은 외부 입력이 동적 웹페이지 생성에 사용될 경우, 전송된 동적 웹페이지를 열람하는 접속자의 권한으로 부적절한 스크립트가 수행되어 정보유출 등의 공격을 유발할 수 있다.

#### 나. 보안대책

외부 입력값 또는 출력값에 스크립트가 삽입되지 못하도록 문자열 치환 함수를 사용하여 & < > " ' /( ) 등을 &amp; &lt; &gt; &quot; &#x27; &#x2F; &#x28; &#x29;로 치환하거나, JSTL 또는 잘 알려진 크로스 사이트 스크립트 방지 라이브러리를 활용한다. HTML 태그를 허용하는 게시판에서는 허용되는 HTML 태그들을 화이트리스트로 만들어 해당 태그만 지원하도록 한다.

#### 다. 코드예제

크로스사이트 스크립트(XSS)는 크게 3가지 공격 방법이 존재한다.

Reflected XSS 공격은 검색 결과, 에러 메시지 등으로 서버가 외부에서 입력받은 악성 스크립트가 포함된 URL 파라미터 값을 사용자 브라우저에서 응답할 때 발생한다. 공격 스크립트가 삽입된 URL을 사용자가 쉽게 확인할 수 없도록 변형하여, 이메일, 메신저, 파일등으로 실행을 유도하는 공격이다.

Stored XSS 공격은 웹 사이트의 게시판, 코멘트 필드, 사용자 프로필 등의 입력 form으로 악성 스크립트를 삽입하여 DB에 저장되면, 사용자가 사이트를 방문하여 저장되어 있는 페이지에 정보를 요청할 때, 서버는 악성 스크립트를 사용자에게 전달하여 사용자 브라우저에서 스크립트가 실행되면서 공격한다.

DOM기반 XSS 공격은 외부에서 입력받은 악성 스크립트가 포한된 URL 파라미터 값이 서버를 거치지 않고, DOM 생성의 일부로 실행되면서 공격한다. Reflected XSS 및 Stored XSS 공격은 서버 애플리케이션 취약점으로 인해, 응답 페이지에 악성 스크립트가 포함되어 브라우저로 전달되면서 공격하는 것인 반면, DOM기반 XSS는 서버와 관계없이 발생하는 것이 차이점이다.

**안전하지 않은 코드의 예 JAVA**

```java
<% String keyword = request.getParameter("keyword"); %>
//외부 입력값에 대하여 검증 없이 화면에 출력될 경우 공격스크립트가 포함된 URL을 생성 할 수 있어
  안전하지 않다.(Reflected XSS)
검색어 : <%=keyword%>

//게시판 등의 입력form으로 외부값이 DB에 저장되고, 이를 검증 없이 화면에 출력될 경우
  공격스크립트가 실행되어 안전하지 않다.(Stored XSS)
검색결과 : $ {m.content}

<script type="text/javascript">
//외부 입력값에 대하여 검증 없이 브라우저에서 실행되는 경우 서버를 거치지 않는 공격스크립트가
  포함된 URL을 생성 할 수 있어 안전하지 않다. (DOM 기반 XSS)
document.write("keyword:" + <%=keyword%>);
</script>
```

외부 입력값 파라미터나 게시판등의 form에 의해 서버의 처리 결과를 사용자 화면에 출력하는 경우, 입력값에 대해서 문자열 치환 함수를 이용하여 스크립트 문자열을 제거하거나, JSTL을 이용하여 출력하거나, 잘 만들어진 외부 XSS 방지 라이브러리를 활용하는 것이 안전하다.

크로스사이트 스크립트의 경우 동작 상황에 따라 동일한 조치방법을 사용하면, 크로스사이트 스크립트 방지는 되더라도 원하는 동작이 정상적으로 되지 않을 수 있기 때문에, 잘 만들어진 외부 XSS방지 라이브러리를 이용하여 각 동작 상황에 따라 적절하게 사용하는 것을 권장한다.

**안전한 코드의 예 JAVA**

```java
<% String keyword = request.getParameter("keyword"); %>
// 방법1. 입력값에 대하여 스크립트 공격가능성이 있는 문자열을 치환한다.
keyword = keyword.replaceAll("&", "&amp;");
keyword = keyword.replaceAll("<", "&lt;");
keyword = keyword.replaceAll(">", "&gt;");
keyword = keyword.replaceAll("￦"", "&quot;");
keyword = keyword.replaceAll("'", "&#x27;");
keyword = keyword.replaceAll("/"", "&#x2F;");
keyword = keyword.replaceAll("(", "&#x28;");

                                    안전한 코드의 예 JAVA

 keyword = keyword.replaceAll(")", "&#x29;");
 검색어 : <%=keyword%>
 //방법2. JSP에서 출력값에 JSTL c:out 을 사용하여 처리한다.
 <%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core"%>
 <%@ taglib uri="http://java.sun.com/jsp/jstl/functions" prefix="fn" %>
 검색결과 : <c:out value="$ {m.content}"/>

 <script type="text/javascript">
 //방법3. 잘 만들어진 외부 라이브러리를 활용(NAVER Lucy-XSS-Filter, OWASP ESAPI,
   OWASP Java-Encoder-Project)
 document.write("keyword:"+
   <%=Encoder.encodeForJS(Encoder.encodeForHTML(keyword))%>);
 </script>
```

다음 C# 코드는 외부 입력값을 출력에 바로 사용하고 있다. 이는 XSS 공격을 유발 할 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
string usrInput = Request.QueryString["ID"];
// 외부 입력 값이 검증 없이 화면에 출력 됩니다.
string str = "ID : " + usrinput;
Request.Write(str);
```

AntiXss 패키지 등을 사용하여 XSS 공격을 예방할 수 있다.

**안전한 코드의 예 C#**

```csharp
string usrInput = Request.QueryString["ID"];
string str = "ID : " + usrinput;
//AntiXss 패키지 등을 이용하여 외부 입력값을 필터링 합니다.
var sanitizedStr = Sanitizer.GetSafeHtmlFragment(str);
quest.Write(sanitizedStr);
```

아래 C 코드 예제는 외부 입력값으로 사용자로부터 받은 입력값을 검증 없이 바로 cgi에 출력하는 화면이다.

**안전하지 않은 코드의 예 C**

```c
int XSS(int argc, char* argv[]) {
    unsigned int i = 0;
    char data[1024];
    …
    // cgiFromString으로 받아온 사용자 입력값이 검증 없이 화면에 출력됩니다.
giFromString(“user input”, data, sizeof(data));
printf(cgiOut, “Print user input = %s<br/>”, data);
    fprintf(cgiOut, “</body></html>￦n”);
    return 0;
}
```

cgi에 출력하기 전에 사용자 입력값을 검증하여야 한다.

**안전한 코드의 예 C**

```c
cgiFromString(“user input”, data, sizeof(data));
// data에 위험한 문자열을 검사하는 코드를 추가한다.
if(strchr(p, ‘<’)) return;
if(strchr(p, ‘>’)) return;
…
fprintf(cgiOut, “Print user input = %s<br/>”, data);
fprintf(cgiOut, “</body></html>￦n”);
```

#### 라. 참고자료

- ① CWE-79 Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting'), MITRE, http://cwe.mitre.org/data/definitions/79.html
- ② Properly encode or escape output, CERT, http://www.securecoding.cert.org/confluence/display/java/IDS51-J.+Properly+encode+or+escape+output
- ③ XSS (Cross Site Scripting) Prevention Cheat Sheet, OWASP, http://www.owasp.org/index.php/XSS_(Cross_Site_Scripting)_Prevention_Cheat_Sheet
- ④ DOM based XSS Prevention Cheat Sheet, OWASP, https://www.owasp.org/index.php/DOM_based_XSS_Prevention_Cheat_Sheet
- ⑤ Understanding Malicious Content Mitigation for Web Developers" http://www.cert.org/tech_tips/malicious_code_mitigation.html
### 5. 운영체제 명령어 삽입

#### 가. 개요

적절한 검증절차를 거치지 않은 사용자 입력값이 운영체제 명령어의 일부 또는 전부로 구성되어 실행되는 경우, 의도하지 않은 시스템 명령어가 실행되어 부적절하게 권한이 변경되거나 시스템 동작 및 운영에 악영향을 미칠 수 있다.

일반적으로 명령어 라인의 파라미터나 스트림 입력 등 외부 입력을 사용하여 시스템 명령어를 생성하는 프로그램이 많이 있다. 하지만 이러한 경우 외부 입력 문자열은 신뢰할 수 없기 때문에 적절한 처리를 해주지 않으면, 공격자가 원하는 명령어 실행이 가능하게 된다.

#### 나. 보안대책

웹 인터페이스로 서버 내부로 시스템 명령어를 전달시키지 않도록 응용프로그램을 구성하고, 외부에서 전달되는 값을 검증 없이 시스템 내부 명령어로 사용하지 않는다. 외부 입력에 따라 명령어 를 생성하거나 선택이 필요한 경우에는 명령어 생성에 필요한 값 들을 미리 지정해 놓고 외부 입력에 따라 선택하여 사용한다.

#### 다. 코드예제

다음의 예제는 Runtime.getRuntime().exec()명령어로 프로그램을 실행하며, 외부에서 전달 되는 인자값은 명령어의 생성에 사용된다. 그러나 해당 프로그램에서 실행할 프로그램을 제한하지 않고 있기 때문에 외부의 공격자는 가능한 모든 프로그램을 실행시킬 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
public static void main(String args[]) throws IOException {
// 해당 프로그램에서 실행할 프로그램을 제한하고 있지 않아 파라미터로 전달되는 모든 프로그램이
   실행될 수 있다.
   String cmd = args[0];
   Process ps = null;
   try {
       ps = Runtime.getRuntime().exec(cmd);
        ...
```

다음의 예제와 같이 미리 정의된 파라미터의 배열을 만들어 놓고, 외부의 입력에 따라 적절한 파라미터를 선택하도록 하여, 외부의 부적절한 입력이 명령어로 사용될 가능성을 배제하여야 한다.

**안전한 코드의 예 JAVA**

```java
public static void main(String args[]) throws IOException {
// 해당 어플리케이션에서 실행할 수 있는 프로그램을 노트패드와 계산기로 제한하고 있다.
  List<String> allowedCommands = new ArrayList<String>();     “
  allowedCommands.add("notepad"); allowedCommands.add("calc");
  String cmd = args[0];
  if (!allowedCommands.contains(cmd)) {
       System.err.println("허용되지 않은 명령어입니다.");
       return;
     }
     Process ps = null; try {
        ps = Runtime.getRuntime().exec(cmd);
                   ......
```

아래 코드는 외부입력값을 검증하지 않고 그대로 명령어로 실행하기 때문에 공격자의 입력에 따라 의도하지 않은 명령어가 실행될 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
//외부로부터 입력받은 값을 검증 없이 사용할 경우 안전하지 않다.

String date = request.getParameter("date");
String command = new String("cmd.exe /c backuplog.bat");
Runtime.getRuntime().exec(command + date);
```

운영체제 명령어 실행 시에는 아래와 같이 외부에서 들어오는 값에 의하여 멀티라인을 지원하는 특수문자(| ; & :)나 파일 리다이렉트 특수문자(> >>)등을 제거하여 원하지 않은 운영체제 명령어가 실행될 수 없도록 필터링을 수행한다.

**안전한 코드의 예 JAVA**

```java
String date = request.getParameter("date");
String command = new String("cmd.exe /c backuplog.bat");
//외부로부터 입력 받은 값을 필터링으로 우회문자를 제거하여 사용한다.
date = date.replaceAll("|","");
date = date.replaceAll(";","");
date = date.replaceAll("&","");
date = date.replaceAll(":","");
date = date.replaceAll(">",""); Runtime.getRuntime().exec(command + date);
```

다음 C# 코드는 외부 입력값을 프로세스가 실행할 파일 이름에 직접 사용하고 있다. 이는 공격자의 입력에 따라 의도하지 않은 명령어가 실행될 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
//외부 입력값이 프로세스가 실행할 파일 이름을 지정하고 있다.
string fileName = PgmTextBox.Text;
ProcessStartInfo proStartInfo = new ProcessStartInfo();
proStartInfo.FileName = fileName;
Process.Start(proStartInfo);
```

적절한 정규식이나, white list 등을 이용하여 검증을 한 후 사용하도록 한다.

**안전한 코드의 예 C#**

```csharp
string fileName = PgmTextBox.Text;
//외부 입력값에 대해 정규식 등을 이용하여 검증해야 한다.
if (Regex.IsMatch(fileName, "properRegexHere"))
{
ProcessStartInfo proStartInfo = new ProcessStartInfo();
proStartInfo.FileName = fileName;
Process.Start(proStartInfo);
}
```

공격자의 입력에 따라 의도하지 않은 명령어가 실행될 수 있다.

**안전하지 않은 코드의 예 C**

```c
int main(int argc, char* argv[]) {
  char cmd[CMD_LENGTH];

    if (argc < 1 ) {
       // error
}
// 외부 입력값으로 커맨드를 직접 수행
cmd_data = argv[1];
snprintf(cmd, CMD_LENGTH, “cat %s”, cmd_data);
system(cmd);
……
}
```

운영체제 명령어 실행 시에는 아래와 같이 외부에서 들어오는 값에 의하여 멀티라인을 지원하는 특수문자(| ; & :)나 파일 리다이렉트 특수문자(> >>)등을 제거하여 원하지 않은 운영체제 명령어가 실행될 수 없도록 필터링을 수행한다.

**안전한 코드의 예 C**

```c
int main(int argc, char* argv[]) {
  char cmd[CMD_LENGTH]; int len = 0;
  if (argc < 1 ) {
    // error
  }
  // 외부 입력값으로 커맨드를 직접 수행 cmd_data = argv[1];
  len = strlen(cmd_data);
for (int i = 0; I < len; i++) {
      if (cmd_data[i] == ‘|’ || cmd_data[i] == ‘&’ ||
          cmd_data[i] == ‘;’ || cmd_data[i] == ‘:’ || cmd_data[i] == ‘>’) {
     // 멀티라인을 지원하는 특수문자나 파일 리다이렉트 특수문자가 존재하여
// 안전하지 않음
    return -1;
   }
}
 snprintf(cmd, CMD_LENGTH, “cat %s”, cmd_data);
 system(cmd);
……
}
```

#### 라. 참고자료

- ① CWE-78 OS Command Injection, MITRE, http://cwe.mitre.org/data/definitions/78.html
- ② Sanitize untrusted data passed to the Runtime.exec() method, CERT, http://www.securecoding.cert.org/confluence/display/java/IDS07-J.+Sanitize +untrusted+data+passed +to+the+Runtime.exec()+method?focusedCommentId=64651588#comment-64651588
- ③ Do not call system(), CERT, http://www.securecoding.cert.org/confluence/pages/viewpage.action?pageId=2130132
- ④ Reviewing Code for OS Injection, OWASP https://www.owasp.org/index.php/Reviewing_Code_for_OS_Injection
### 6. 위험한 형식 파일 업로드

#### 가. 개요

서버 측에서 실행될 수 있는 스크립트 파일(asp, jsp, php 파일 등)이 업로드가능하고, 이 파일을 공격자가 웹으로 직접 실행시킬 수 있는 경우, 시스템 내부명령어를 실행하거나 외부와 연결하여 시스템을 제어할 수 있는 보안약점이다.

#### 나. 보안대책

화이트 리스트 방식으로 허용된 확장자만 업로드를 허용한다. 업로드 되는 파일을 저장할 때에는 파일명과 확장자를 외부사용자가 추측할 수 없는 문자열로 변경하여 저장하며, 저장 경로는 ‘web document root’ 밖에 위치시켜서 공격자의 웹으로 직접 접근을 차단한다. 또한 파일 실행 여부를 설정할 수 있는 경우, 실행 속성을 제거한다.

#### 다. 코드예제

업로드할 파일에 대한 유효성을 검사하지 않으면, 위험한 유형의 파일을 공격자가 업로드하거나 전송할 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
   MultipartRequest multi
   = new MultipartRequest(request,savePath,sizeLimit,"euc-kr",new
 DefaultFileRenamePolicy());
 ......
 //업로드 되는 파일명을 검증없이 사용하고 있어 안전하지 않다.
       String fileName = multi.getFilesystemName("filename");
   ......
       sql = " INSERT INTO
   board(email,r_num,w_date,pwd,content,re_step,re_num,filename) "
           + " values ( ?, 0, sysdate(), ?, ?, ?, ?, ? ) ";
     preparedStatement pstmt = con.prepareStatement(sql);
 pstmt.setString(1, stemail);
 pstmt.setString(2, stpwd);

                              안전하지 않은 코드의 예 JAVA

pstmt.setString(3, stcontent);
pstmt.setString(4, stre_step);
pstmt.setString(5, stre_num);
pstmt.setString(6, fileName);
pstmt.executeUpdate();
Thumbnail.create(savePath+"/"+fileName, savePath+"/"+"s_"+fileName, 150);
```

아래 코드는 업로드 파일의 확장자를 검사하여 허용되지 않은 확장자인 경우 업로드를 제한하고 있다.

**안전한 코드의 예 JAVA**

```java
MultipartRequest multi
      = new MultipartRequest(request,savePath,sizeLimit,"euc-kr",new
    DefaultFileRenamePolicy());
    ......
      String fileName = multi.getFilesystemName("filename");
      if (fileName != null) {
//1.업로드 파일의 마지막 “.” 문자열의 기준으로 실제 확장자 여부를 확인하고, 대소문자 구별을
    해야한다.
       String fileExt =
         FileName.substring(fileName.lastIndexOf(".")+1).toLowerCase();
//2.되도록 화이트 리스트 방식으로 허용되는 확장자로 업로드를 제한해야 안전하다.
    if (!"gif".equals(fileExt) && !"jpg".equals(fileExt) && !"png".equals(fileExt))
{
             alertMessage("업로드 불가능한 파일입니다.");
             return;
         }
}
......
      sql = " INSERT INTO
board(email,r_num,w_date,pwd,content,re_step,re_num,filename) "
     + " values ( ?, 0, sysdate(), ?, ?, ?, ?, ? ) ";
PreparedStatement pstmt = con.prepareStatement(sql);
......
   Thumbnail.create(savePath+"/"+fileName, savePath+"/"+"s_"+fileName, 150);
```

업로드할 파일에 대한 유효성을 검사하지 않으면, 위험한 유형의 파일을 공격자가 업로드 하거나 전송할 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
string fn = Path.GetFileName(FileUploadCtr.FileName);
//업로드 하는 파일명을 검증없이 사용하고 있다.
FileUploadCtr.SaveAs(fn);
StatusLabel.Text = "Upload status: File uploaed!";
```

파일 타입과 크기 등을 검사하여 제한하도록 한다.

**안전한 코드의 예 C#**

```csharp
//파일 타입과 크기를 제한합니다.
if (FileUploadCtr.PostedFile.ContentType == "image/jpeg”)
{
    if (FileUploadCtr.PostedFile.ContentLength < 102400)
    {
        string fn = Path.GetFileName(FileUploadCtr.FileName);
        FileUploadCtr.SaveAs(Server.MapPath("~/") + fn);
        StatusLabel.Text = "Upload status: File uploaed!";
}
else
        StatusLabel.Text = "Upload Status: The File has to be less than
    100 kb!";
}
else
StatusLabel.Text = "Upload Status: Only JPEG files are accepted!";
```

#### 라. 참고자료

- ① CWE-434 Unrestricted Upload of File with Dangerous Type, MITRE, http://cwe.mitre.org/data/definitions/434.html
- ② Prevent arbitrary file upload, CERT, http://www.securecoding.cert.org/confluence/display/java/IDS56-J.+Prevent+arbitrary+file+upload
- ③ Secure File Upload Check List With PHP, Clay, http://hungred.com/useful-information/secure-file-upload-check-list-php/
- ④ Unrestricted File Upload, OWASP https://www.owasp.org/index.php/Unrestricted_File_Upload
### 7. 신뢰되지 않는 URL 주소로 자동접속 연결

#### 가. 개요

사용자로부터 입력되는 값을 외부사이트의 주소로 사용하여 자동으로 연결하는 서버 프로그램은 피싱(Phishing) 공격에 노출되는 취약점을 가질 수 있다.

일반적으로 클라이언트에서 전송된 URL 주소로 연결하기 때문에 안전하다고 생각할 수 있으나, 공격자는 해당 폼의 요청을 변조함으로써 사용자가 위험한 URL로 접속할 수 있도록 공격할 수 있다.

#### 나. 보안대책

자동 연결할 외부 사이트의 URL과 도메인은 화이트 리스트로 관리하고, 사용자 입력값을 자동 연결할 사이트 주소로 사용하는 경우에는 입력된 값이 화이트 리스트에 존재하는지 확인해야 한다.

#### 다. 코드예제

다음과 같은 코드가 서버에 존재할 경우 공격자는 아래와 같은 링크로 희생자가 피싱 사이트 등으로 접근하도록 할 수 있다.

(예시 링크)

<a href="http://bank.example.com/redirect?url=http://attacker.example.net">Click</a>

**안전하지 않은 코드의 예 JAVA**

```java
 String id = (String)session.getValue("id");
 String bn = request.getParameter("gubun");
 //외부로부터 입력받은 URL이 검증없이 다른 사이트로 이동이 가능하여 안전하지 않다.
 String rd = request.getParameter("redirect");
 if (id.length() > 0) {
        String sql = "select level from customer where customer_id = ? ";
      conn = db.getConnection();
      pstmt = conn.prepareStatement(sql);

                                안전하지 않은 코드의 예 JAVA

         pstmt.setString(1, id);
         rs = pstmt.executeQuery();
rs.next();
if ("0".equals(rs.getString(1)) && "01AD".equals(bn)) {
          response.sendRedirect(rd);
          return;
}
```

다음의 예제와 같이, 외부로 연결할 URL과 도메인들은 화이트 리스트를 작성한 후, 그 중에서 선택하도록 함으로써 안전하지 않은 사이트로의 접근을 차단할 수 있다.

**안전한 코드의 예 JAVA**

```java
//이동 할 수 있는 URL범위를 제한하여 피싱 사이트 등으로 이동하지 못하도록 한다.
String allowedUrl[] = { "/main.do", "/login.jsp", "list.do" };
......
String rd = request.getParameter("redirect");
try {
     rd = allowedUrl[Integer.parseInt(rd)];
} catch(NumberFormatException e) {
    return "잘못된 접근입니다.";
} catch(ArrayIndexOutOfBoundsException e) {
     return "잘못된 입력입니다.";
}
if (id.length() > 0) {
......
         if ("0".equals(rs.getString(1)) && "01AD".equals(bn)) {
               response.sendRedirect(rd);
             return;
}
```

외부 입력 값으로 받은 URL로 검증없이 연결되는 경우, 공격자의 입력에 따라 피싱사이트 등으로 연결될 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
// 외부 입력값으로 받은 URL을 검증없이 연결하고 있다.
string url = Request["dest"];
Response.Redirect(url);
```

로컬 URL 검증이나 white list 등을 이용하여 검증이 필요하다.

**안전한 코드의 예 C#**

```csharp
public void AttackOpenRedirect()
   {
          String url = Request["dest"];
// 외부 입력값이 로컬 URL인지 확인한다. MVC 3 이상의 프레임워크를 사용할 경우,
  System.Web.Mvc 에 정의되어있는 Url.isLocalUrl 을 바로 사용할 수 있다.
     if(isLocalUri(url)) Response.Redirect(url);
      }
   private bool IsLocalUrl(string url)
   {
      if(string.IsNullOrEmpty(url))
      {
       return false;
      }
   Uri absoluteUri;
   if(Uri.TryCreate(url, UriKind.Absolute, out absoluteUri))
  {
     return String.Equals(this.Request.Url.Host, absoluteUri.Host,
  StringComparison.OrdinalIgnoreCase);
  }
else
 {
      bool isLocal = !url.StartsWith("http:",
 StringComparison.OrdinalIgnoreCase)

                                         안전한 코드의 예 C#

          && !url.StartsWith("https:",
    StringComparison.OrdinalIgnoreCase)
         && Uri.IsWellFormedUriString(url, UriKind.Relative);
        return isLocal;
    }
}
```

#### 라. 참고자료

- ① CWE-601 URL Redirection to Untrusted Site, MITRE, http://cwe.mitre.org/data/definitions/601.html
- ② Unvalidated Redirects and Forwards Cheat Sheet, OWASP https://www.owasp.org/index.php/Unvalidated_Redirects_and_Forwards_Cheat_Sheet
### 8. 부적절한 XML 외부개체 참조

#### 가. 개요

XML 문서에는 DTD(Document Type Definition)를 포함할 수 있으며, DTD는 XML 엔티티 (entitiy)*를 정의한다. 부적절한 XML 외부개체 참조 보안약점은 서버에서 XML 외부 엔티티를 처리할 수 있도록 설정된 경우에 발생할 수 있다.

취약한 XML parser가 외부 값을 참조하는 XML 값을 처리할 때, 공격자가 삽입한 공격 구문이 동작되어 서버 파일 접근, 불필요한 자원 사용, 인증 우회, 정보 노출 등이 발생 할 수 있다.

* 반복적인 문장이나 문자열을 저장해놓고 쉽게 참조할 수 있도록 함

#### 나. 보안대책

로컬 정적 DTD를 사용하도록 설정하고, 외부에서 전송된 XML문서에 포함된 DTD를 완전하게 비활성화해야 한다. 비활성화를 할 수 없는 경우에는 외부 엔티티 및 외부 문서 유형 선언을 각 파서에 맞는 고유한 방식으로 비활성화 한다.

#### 다. 코드예제

다음의 예제는 XML 소스를 읽어서 분석하는 소스코드이다. 공격자가 아래와 같이 XML 외부 엔티티를 참조하는 recivedXML 데이터를 전송하고, 이를 파싱할 때 /etc/passwd 파일을 참조할 수 있다.

receivedXML <?xml version="1.0" encoding="ISO-8859-1"?> <!DOCTYPE foo [ <!ELEMENT foo ANY > <!ENTITY xxe SYSTEM "file:///etc/passwd" >]><foo>&xxe;</foo>

**안전하지 않은 코드의 예 JAVA**

```java
 public void unmarshal(File receivedXml)
 throws JAXBException, ParserConfigurationException, SAXException, IOException {
          JAXBContext jaxbContext = JAXBContext.newInstance( Student.class );
          Unmarshaller jaxbUnmarshaller = jaxbContext.createUnmarshaller();
          // 입력받은 receivedXml 을 이용하여 Document를 생성한다.
          DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
          dbf.setNamespaceAware(true);
          DocumentBuilder db = dbf.newDocumentBuilder();
          Document document = db.parse(receivedXml);
         // 외부 엔티티로 만들어진 document를 이용하여 마샬링을 수행하여 안전하지
         않다.
          Student employee = (Student) jaxbUnmarshaller.unmarshal( document );
}
```

다음 예제는 class XXE에서 외부개체 참조 제한 설정 없이 secure.xml을 참조하고 있다. 이 때, secure.xml이 아래와 같을 때 /dev/tty 콘솔이 실행되어 입력 요청을 대기하는 서비스 거부 공격이 발생할 수 있다.

secure.xml <?xml version="1.0"?> <!DOCTYPE foo SYSTEM "file:/dev/tty"> <foo>bar</foo>

**안전하지 않은 코드의 예 JAVA**

```java
 import javax.xml.parsers.SAXParsers;
 import javax.xml.parsers.SAXParserFactory;

 class XXE {
         public static void main(String[] args)
          throws FileNotFoundException, ParserConfigurationException, SAXException,
IOException {

                            안전하지 않은 코드의 예 JAVA

 SAXParserFactory factory = SAXParserFactory.newInstance();
            SAXParser saxParser = factory.newSAXParser();
            // 외부개체 참조 제한 설정 없이 secure.xml 파일을 읽어서 파싱하여 안전하지 않다.
           saxParser.parse(new FileInputStream("secure.xml"), new DefaultHandler());
     }
 }
```

다음의 JAXP DocumentBuilderFactory를 사용하는 경우 아래와 같이 제한 설정 추가할 수 있다.

**안전한 코드의 예 JAVA**

```java
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
// XML 파서가 doctype을 정의하지 못하도록 설정한다.
dbf.setFeature("http://apache.org/xml/featuresdisallow-doctype-decl", true);
// 외부 일반 엔티티를 포함하지 않도록 설정한다.
dbf.setFeature("http://xml.org/sax/features/external-general-entities", false);
// 외부 파라미터도 포함하지 않도록 설정한다.
dbf.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
// 외부 DTD 비활성화한다.
dbf.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
// XIncude를 사용하지 않는다.
dbf.setXIncludeAware(false);
// 생성된 파서가 엔티티 참조 노드를 확장하지 않도록 한다.
dbf.setExpandEntityReferences(false);
DocumentBuilder db = dbf.newDocumentBuilder();
Document document = db.parse(receivedXml);
Model model = (Model) u.unmarshal(document);
```

PHP에서는 libxml_disable_entity_loader 함수를 이용하여 외부 엔티티 사용을 비활성화 할 수 있다.

**안전한 코드의 예 JAVA**

```java
value = libxml_disable_entity_loader(true);
$dom = new DOMDocument();
$dom -> loadXML($xml);
libxml_disable_entity_loader($value);
```

#### 라. 참고자료

- ① CWE-611: Improper Restriction of XML External Entity Reference, MITRE, https://cwe.mitre.org/data/definitions/611.html
- ② XML Entity Prevention Cheet Sheet, OWASP, https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html
### 9. XML 삽입

#### 가. 개요

검증되지 않은 외부 입력 값이 XQuery 또는 XPath 쿼리문을 생성하는 문자열로 사용되어 공격자가 쿼리문의 구조로 임의로 변경하고 임의의 쿼리를 실행하여 허가되지 않은 데이터를 열람하거나 인증절차를 우회할 수 있는 보안약점이다.

#### 나. 보안대책

XQuery 또는 Xpath 쿼리에 사용되는 외부 입력데이터에 대하여 특수문자 및 쿼리 예약어를 필터링하고 파라미터화된 쿼리문을 지원하는 XQuery를 사용한다.

#### 다. 코드예제

- XQuery 삽입
다음의 예제에서는 executeQuery으로 생성하는 쿼리의 파라미터의 일부로 외부입력값 name)을 사용하고 있다. 만일 something' or '1'='1 을 name의 값으로 전달하면 다음과 같은 쿼리문을 수행할 수 있으며, 이 경우 파일 내의 모든 값을 출력할 수 있게 된다.

doc('users.xml')/userlist/user[uname='something' or ‘1’=‘1’

**안전하지 않은 코드의 예 JAVA**

```java
// 외부 입력 값을 검증하지 않고 XQuery 표현식에 사용한다.
String name = props.getProperty("name");
.......
// 외부 입력 값에 의해 쿼리 구조가 변경 되어 안전하지 않다.
String es = "doc('users.xml')/userlist/user[uname='"+name+"']";
XQPreparedExpression expr = conn.prepareExpression(es);
XQResultSequence result = expr.executeQuery();
```

다음의 예제에서는 외부 입력값을 받고 해당 값 기반의 XQuery상의 쿼리 구조를 변경시키지 않는 bindString 함수를 이용함으로써 외부 입력값으로 쿼리 구조가 변경될 수 없도록 한다.

**안전한 코드의 예 JAVA**

```java
1. // blingString 함수로 쿼리 구조가 변경되는 것을 방지한다.
2. String name = props.getProperty("name");
3. .......
4. String es = "doc('users.xml')/userlist/user[uname='$xname']";
5. XQPreparedExpression expr = conn.prepareExpression(es);
6. expr.bindString(new QName("xname"), name, null);
7. XQResultSequence result = expr.executeQuery();
```

다음의 C# 코드도 외부입력 값을 이용하여 XQuery 문을 만들고 있다.

**안전하지 않은 코드의 예 C#**

```csharp
//외부 입력 값으로 XQuery 문을 만든다.
String squery =
        "for $user in doc(users.xml)//user[username='"
        + UserTextBox.Text
        + "'and pass='"
        + PwdTextBox.Text
        + "'] return $user";

    Processor processor = new Processor();

    XQueryCompiler compiler = processor.NewXQueryCompiler();

    XdmNode indoc = processor.NewDocumentBuilder().Build(new
Uri(Server.MapPath("users.xml")));
using (StreamReader query = new StreamReader(squery))
{
    XQueryCompiler compiler = processor.NewXQueryCompiler();
    XQueryExecutable exp = compiler.Compile(query.ReadToEnd());

                               안전하지 않은 코드의 예 C#

     XQueryEvaluator eval = exp.Load();
     eval.ContextItem = indoc;

     Serializer qout = new Serializer();
     qout.SetOutputProperty(Serializer.METHOD, "xml");
     qout.SetOutputProperty(Serializer.DOCTYPE_PUBLIC, "-//W3C//DTD
 XHTML 1.0 Strict//EN");
     qout.SetOutputProperty(Serializer.DOCTYPE_SYSTEM,
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd");
     qout.SetOutputProperty(Serializer.INDENT, "yes");
     qout.SetOutputProperty(Serializer.OMIT_XML_DECLARATION, "no");

    qout.SetOutputWriter(Response.Output);
 //별다른 검증없이 XML 데이터에 접근한다.
     eval.Run(qout);
 }
```

문자열 필터링으로 쿼리문 조작을 막을 수 있다.

**안전한 코드의 예 C#**

```csharp
 String squery =
         "for $user in doc(users.xml)//user[username='"
         + UserTextBox.Text
         + "'and pass='"
         + PwdTextBox.Text
         + "'] return $user";
 // 문자열 필터링으로 위험한 문자열을 제거한다.
string validatedQuery = squery.Replace('/','*');
    Processor processor = new Processor();
 XQueryCompiler compiler = processor.NewXQueryCompiler();

    XdmNode indoc = processor.NewDocumentBuilder().Build(new
    Uri(Server.MapPath("users.xml")));
    using (StreamReader query = new StreamReader(validatedQuery))

                                    안전한 코드의 예 C#

    { // tainted value propagated
        XQueryCompiler compiler = processor.NewXQueryCompiler();
        XQueryExecutable exp = compiler.Compile(query.ReadToEnd()); //
xquery created
        XQueryEvaluator eval = exp.Load();
        eval.ContextItem = indoc;

        Serializer qout = new Serializer();
        qout.SetOutputProperty(Serializer.METHOD, "xml");
        qout.SetOutputProperty(Serializer.DOCTYPE_PUBLIC, "-//W3C//DTD
   XHTML 1.0 Strict//EN");
        qout.SetOutputProperty(Serializer.DOCTYPE_SYSTEM,
   "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd");
       qout.SetOutputProperty(Serializer.INDENT, "yes");
        qout.SetOutputProperty(Serializer.OMIT_XML_DECLARATION, "no");

        qout.SetOutputWriter(Response.Output);
        eval.Run(qout);
    }
```

- XPath 삽입
아래 예제에서는 nm과 pw에 대한 입력값 검증을 수행하지 않으므로 nm의 값으로 "tester", pw의 값으로 "x' or 'x'='x"을 전달하면 아래와 같은 질의문이 생성되어 인증과정을 거치지 않고 로그인할 수 있다.

"//users/user[login/text()='tester' and password/text()='x' or //'x'='x']/home_dir/text()“

**안전하지 않은 코드의 예 JAVA**

```java
// 프로퍼티로부터 외부 입력값 name과 password를 읽어와 각각 nm, pw변수에 저장
String nm = props.getProperty("name");
String pw = props.getProperty("password");
......
XPathFactory factory = XPathFactory.newInstance();

                             안전하지 않은 코드의 예 JAVA

XPath xpath = factory.newXPath();
......
// 검증되지 않은 입력값 외부 입력값 nm, pw 를 사용하여 안전하지 않은 질의문이 작성되어 expr
    변수에 저장된다.
XPathExpression expr = xpath.compile("//users/user[login/text()='"+nm+"' and
    password/text()='"+pw+"']/home_dir/text()");

// 안전하지 않은 질의문이 담긴 expr을 평가하여 결과를 result에 저장한다.
Object result = expr.evaluate(doc, XPathConstants.NODESET);
// result의 결과를 NodeList 타입으로 변환하여 nodes 저장한다.
NodeList nodes = (NodeList) result;
for (int i=0; i<nodes.getLength(); i++) {
     String value = nodes.item(i).getNodeValue();
     if (value.indexOf(">") < 0) {
         // 공격자가 이름과 패스워드를 확인할 수 있다. System.out.println(value);
     }
}
```

다음의 예제는 XQuery를 사용하여 미리 쿼리 골격을 생성함으로써 외부입력으로 인해 쿼리 구조가 바뀌는 것을 막을 수 있다.

**안전한 코드의 예 JAVA**

```java
 [ login.xq 파일 ]
 declare variable $loginID as xs:string external; declare variable $password as xs:string
 external;

 //users/user[@loginID=$loginID and @password=$password]
 // XQuery를 이용한 XPath Injection 방지
 String nm = props.getProperty("name");
 String pw = props.getProperty("password");
 Document doc = new Builder().build("users.xml");

 // 파라미터화된 쿼리가 담겨있는 login.xq를 읽어와서 파라미터화된 쿼리를 생성한다.
 XQuery xquery = new XQueryFactory().createXQuery(new File("login.xq"));

                                    안전한 코드의 예 JAVA

Map vars = new HashMap();
// 검증되지 않은 외부값인 nm, pw를 파라미터화된 쿼리의 파라미터로 설정한다.
vars.put("loginID", nm);
vars.put("password", pw);
// 파라미터화된 쿼리를 실행하므로 외부값을 검증없이 사용하여도 안전하다.
Nodes results = xquery.execute(doc, null, vars).toNodes();
for (int i=0; i<results.size(); i++) {
         System.out.println(results.get(i).toXML());
}
```

파라미터화된 쿼리를 지원하는 XQuery 구문으로 대체할 수 없는 경우에는 XPath 삽입을 유발할 수 있는 문자들을 입력값에서 제거하고 XPath 구문을 생성, 실행하도록 한다.

**안전한 코드의 예 JAVA**

```java
// XPath 삽입을 유발할 수 있는 문자들을 입력값에서 제거
public String XPathFilter(String input) {
    if (input != null) return input.replaceAll("[',￦￦[]", "");
    else return "";
}
......
// 외부 입력값에 사용
String nm = XPathFilter(props.getProperty("name"));
String pw = XPathFilter(props.getProperty("password"));
......
XPathFactory factory = XPathFactory.newInstance();
XPath xpath = factory.newXPath();
......
// 외부 입력값인 nm, pw를 검증하여 쿼리문을 생성하므로 안전하다.
XPathExpression expr = xpath.compile("//users/user[login/text()='"+nm+"' and
 password/text()='"+pw+"']/home_dir/text()");
Object result = expr.evaluate(doc, XPathConstants.NODESET);
NodeList nodes = (NodeList) result;
for (int i=0; i<nodes.getLength(); i++) {

                                     안전한 코드의 예 JAVA

     String value = nodes.item(i).getNodeValue();
     if (value.indexOf(">") < 0) {
          System.out.println(value);
     }
 }
     ......
```

아래 코드는 입력값을 검증하지 않고 입력값을 XPath 구문 생성 및 실행에 사용하고 있다. 입력 값으로 any' or 'a' = 'a 와 같이 XPath 구문을 조작하는 문자열을 전달하는 경우 //food[name ='any' or 'a' = 'a']/price 같이 구문이 만들어지고 실행되어 모든 food의 가격(price)가 조회되게 된다.

**안전하지 않은 코드의 예 JAVA**

```java
public static void main(String[] args) throws Exception {
   if (args.length <= 0) {
         System.err.println("가격을 검색할 식품의 이름을 입력하세요."); return;
    }
    String name = args[0];
    DocumentBuilder docBuilder =
 DocumentBuilderFactory.newInstance().newDocumentBuilder();
Document doc = docBuilder.parse("http://www.w3schools.com/xml/simple.xml");
    Xpath xpath = XPathFactory.newInstance().newXPath();
// 프로그램의 커맨드 옵션으로 입력되는 외부값 name을 사용하여 쿼리문을 직접 작성하여 수행하므로 안전하지 않다.
   NodeList nodes = (NodeList) xpath.evaluate(“//food[name=‘” + name +
     “’]/price”, doc, XPathConstants.NODESET);
    for (int i = 0; i < nodes.getLength(); i++) {
          System.out.println(nodes.item(i).getTextContent());
    }
}
```

외부 입력값을 XPath 구문 생성 및 실행에 사용하는 경우 XPath 구문을 조작할 수 있는 문자열을 제거하고 사용할 수 있도록 한다.

**안전한 코드의 예 JAVA**

```java
public static void main(String[] args) throws Exception {
    if (args.length <= 0) {
        System.err.println("가격을 검색할 식품의 이름을 입력하세요.");
        return;
    }
/*프로그램의 커맨드 옵션으로 입력되는 외부값 name에서 XPath 구문을 조작할 수 있는 문자를
    제거하는 검증을 수행하여 안전하다.*/
    String name = args[0];
    if (name != null) {
        name = name.replaceAll("[()￦￦-'￦￦[￦￦]:,*/]", "");
    }
 DocumentBuilder docBuilder =
 DocumentBuilderFactory.newInstance().newDocumentBuilder();
    Document doc = docBuilder.parse("http://www.w3schools.com/xml/simple.xml");
    XPath xpath = XPathFactory.newInstance().newXPath();
    NodeList nodes = (NodeList) xpath.evaluate(“//food[name='" + name + "']/price",
doc, XPathConstants.NODESET);
    for (int i = 0; i < nodes.getLength(); i++) {
       System.out.println(nodes.item(i).getTextContent());
    }
}
```

다음의 예제는 외부입력을 사용하여 XPath 식에 바로 사용한다. 이는 공격자의 입력에 따라 XQuery의 구조를 바꾸어 예기치 않은 공격이 발생할 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
string acctID = Request["acctID"];
string query = null; if(acctID != null)
{
StringBuffer sb = new StringBuffer("/accounts/account[acctID='"); sb.Append(acctID);

                              안전하지 않은 코드의 예 C#

 sb.Append("']/email/text()"); query = sb.ToString();

 }

 XPathDocument docNav = new XPathDocument(myXml); XPathNavigator nav =
 docNav.CreateNavigator();
 //외부 입력값을 검증없이 사용하고 있습니다.
 nav.Evaluate(query);
```

다음의 예제는 XPathExpression을 사용하여 미리 쿼리 골격을 생성함으로써 외부입력으로 인해 쿼리 구조가 바뀌는 것을 막을 수 있다.

**안전한 코드의 예 C#**

```csharp
string xpath = "/accounts/account[@acctID=$acctID]/email/text()";
XPathExpression expr = DynamicContext.Compile(xpath);
DynamicContext ctx = new DynamicContext();
ctx.AddVariable("acctID", AccountIDTextBox.Text);
expr.SetContext(ctx);
XPathNodeIterator data = nav.Select(expr);
```

#### 라. 참고자료

- ① CWE-652 XQuery Injection, MITRE, http://cwe.mitre.org/data/definitions/652.html
- ② Prevent XML Injection, CERT,http://www.securecoding.cert.org/confluence/display/java/IDS16- J.+Prevent+XML+Injection
- ③ CWE-643 XPath Injection, MITRE, http://cwe.mitre.org/data/definitions/643.html
- ④ Prevent XPath Injection, CERT, http://www.securecoding.cert.org/confluence/display/java/IDS53-J.+Prevent+XPath+Injections
- ⑤ XPATH Injection, OWASP, https://www.owasp.org/index.php/XPATH_Injection
### 10. LDAP 삽입

#### 가. 개요

공격자가 외부 입력으로 의도하지 않은 LDAP(Lightweight Directory Access Protocol) 명령어를 수행할 수 있다. 즉, 웹 응용프로그램이 사용자가 제공한 입력을 올바르게 처리하지 못하면, 공격자가 LDAP 명령문의 구성을 바꿀 수 있다. 이로 인해 프로세스가 명령을 실행한 컴포넌트와 동일한 권한(Permission)을 가지고 동작하게 된다.

외부 입력값을 적절한 처리 없이 LDAP 쿼리문이나 결과의 일부로 사용하는 경우, LDAP 쿼리문이 실행될 때 공격자는 LDAP 쿼리문의 내용을 마음대로 변경할 수 있다.

#### 나. 보안대책

DN(Distinguished Name)과 필터에 사용되는 사용자 입력값에는 특수문자가 포함되지 않도록 특수문자를 제거한다. 만약 특수문자를 사용해야 하는 경우에는 특수문자( = + < > # ; ￦ 등 )가 실행명령이 아닌 일반문자로 인식되도록 처리한다.

#### 다. 코드예제

userSN과 userPassword 변수의 값으로 *을 전달할 경우 필터 문자열은 “(&(sn=S*) userPassword=*))”가 되어 항상 참이 되며 이는 의도하지 않은 동작을 유발시킬 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
private void searchRecord(String userSN, String userPassword) throws
   NamingException {
   Hashtable<String, String> env = new Hashtable<String, String>();
   env.put(Context.INITIAL_CONTEXT_FACTORY,
"com.sun.jndi.ldap.LdapCtxFactory");
   try {
           DirContext dctx = new InitialDirContext(env);
           SearchControls sc = new SearchControls();
           String[] attributeFilter = { "cn", "mail" };

                                 안전하지 않은 코드의 예 JAVA

sc.setReturningAttributes(attributeFilter);
             sc.setSearchScope(SearchControls.SUBTREE_SCOPE);
             String base = "dc=example,dc=com";
/*userSN과 userPassword 값에 LDAP필터를 조작할 수 있는 공격 문자열에 대한 검증이 없어
    안전하지 않다.*/
             String filter = "(&(sn=" + userSN + ")(userPassword=" + userPassword + "))";
             NamingEnumeration<?> results = dctx.search(base, filter, sc);
             while (results.hasMore()) {
                 SearchResult sr = (SearchResult) results.next();
                 Attributes attrs = sr.getAttributes();
                 Attribute attr = attrs.get("cn");
    .....
            }
            dctx.close();
     } catch (NamingException e) { … }
}
```

검색을 위한 필터 문자열로 사용되는 외부의 입력에서 위험한 문자열을 제거하여 위험성을 부분적으로 감소시킬 수 있다.

**안전한 코드의 예 JAVA**

```java
 private void searchRecord(String userSN, String userPassword) throws
     NamingException {
      Hashtable<String, String> env = new Hashtable<String, String>();
      env.put(Context.INITIAL_CONTEXT_FACTORY,
 "com.sun.jndi.ldap.LdapCtxFactory");
    try {
             DirContext dctx = new InitialDirContext(env);
             SearchControls sc = new SearchControls();
             String[] attributeFilter = {"cn", "mail" };
             sc.setReturningAttributes(attributeFilter);
 sc.setSearchScope(SearchControls.SUBTREE_SCOPE);
        String base = "dc=example,dc=com";

                                    안전한 코드의 예 JAVA

 // userSN과 userPassword 값에서 LDAP 필터를 조작할 수 있는 문자열을 제거하고 사용
             if (!userSN.matches("[￦￦w￦￦s]*") || !userPassword.matches("[￦￦w]*")) {
                  throw new IllegalArgumentException("Invalid input");
              }
              String filter = "(&(sn=" + userSN + ")(userPassword=" + userPassword + "))";
              NamingEnumeration<?> results = dctx.search(base, filter, sc);
              while (results.hasMore()) {
                   SearchResult sr = (SearchResult) results.next();
                   Attributes attrs = sr.getAttributes();
         Attribute attr = attrs.get("cn");
    ......
         }
         dctx.close();
      } catch (NamingException e) { … }
}
```

다음은 인증하지 않은 익명 바인딩으로 LDAP 쿼리를 실행하는 C# 코드 예제이다.

**안전하지 않은 코드의 예 C#**

```csharp
static void SearchRecord(string userSN, string userPW)
{
try {
    DirectoryEntry oDE;
    oDE = new DirectoryEntry(GetStrPath());
    // 인증을 하지않은 익명 바인딩으로 LDAP 쿼리를 실행
    foreach(DirectoryEntry objChildDE om oDE.Children) {
...
}
             } catch (NamingException e) { ... }
}
```

익명 바인딩을 사용하지 않고 인증을 진행해야 한다.

**안전한 코드의 예 C#**

```csharp
void LDAPInjection() {
    char *filter = getenv(“Filter”);
    int error_code;
    LDAP *ld = NULL;
    LDAPMessage *result;
    // 외부에서 불러온 filter를 검증없이 사용
    error_code = ldap_search_ext_s(ld, FIND_DN, LDAP_SCOPE_BASE, filter,
    NULL, 0, NULL, NULL, LDAP_NO_LIMIT, LDAP_NO_LIMIT, &result);
}
```

아래 C 코드는 외부에서 불러온 filter를 LDAP 탐색에 그대로 사용하고 있다. LDAP 필터에 OR 연산 등을 사용하여 의도치 않은 동작이 발생할 수 있다.

**안전하지 않은 코드의 예 C**

```c
void LDAPInjection() {
  char *filter = getenv(“Filter”);
    int error_code;
    LDAP *ld = NULL;
    LDAPMessage *result;
    // 외부에서 불러온 filter를 검증없이 사용
    error_code = ldap_search_ext_s(ld, FIND_DN, LDAP_SCOPE_BASE, filter,
    NULL, 0, NULL, NULL, LDAP_NO_LIMIT, LDAP_NO_LIMIT, &result);
}
```

공격 가능성이 있는 문자열을 필터하여 문제를 해결할 수 있다.

**안전한 코드의 예 C**

```c
void LDAPInjection() {
char *filter = getenv(“Filter”);
int error_code; int i;
LDAP *ld = NULL;
LDAPMessage *result;
// 정보를 알고 싶은 사용자의 이름을 고정 값으로 사용
    for(i = 0; *(filter + i) != 0; i++) {
// 공격 가능한 문자열 검사
 switch(*(filter + i)) {
        case ‘*’:
        case ‘(’:
        case ‘)’:
    …
          return;
    }
}
error_code = ldap_search_ext_s(ld, FIND_DN, LDAP_SCOPE_BASE, filter,
NULL, 0, NULL, NULL, LDAP_NO_LIMIT, LDAP_NO_LIMIT, &result);
}
```

#### 라. 참고자료

- ① CWE-90 LDAP Injection, MITRE, http://cwe.mitre.org/data/definitions/90.html
- ② Prevent LDAP injection, CERT, http://www.securecoding.cert.org/confluence/display/java/IDS54-J.+Prevent+LDAP+injection
- ③ LDAP injection, OWASP https://www.owasp.org/index.php/LDAP_Injection_Prevention_Cheat_Sheet
- ④ “LDAP Resources” http://ldapman.org/
### 11. 크로스사이트 요청 위조

#### 가. 개요

특정 웹사이트에 대해서 사용자가 인지하지 못한 상황에서 사용자의 의도와는 무관하게 공격자가 의도한 행위(수정, 삭제, 등록 등)를 요청하게 하는 공격을 말한다. 웹 응용프로그램이 사용자로부터 받은 요청에 대해서 사용자가 의도한 대로 작성되고 전송된 것인지 확인하지 않는 경우 발생 가능 하고 특히 해당 사용자가 관리자인 경우 사용자 권한관리, 게시물삭제, 사용자 등록 등 관리자 권한 으로만 수행 가능한 기능을 공격자의 의도대로 실행시킬 수 있게 된다.

공격자는 사용자가 인증한 세션이 특정 동작을 수행하여도 계속 유지되어 정상적인 요청과 비정상 적인 요청을 구분하지 못하는 점을 악용한다. 웹 응용프로그램에 요청을 전달할 경우, 해당 요청의 적법성을 입증하기 위하여 전달되는 값이 고정되어 있고 이러한 자료가 GET 방식으로 전달된다면 공격자가 이를 쉽게 알아내어 원하는 요청을 보냄으로써 위험한 작업을 요청할 수 있게 된다.

#### 나. 보안대책

입력화면 폼 작성 시 GET 방식보다는 POST 방식을 사용하고 입력화면 폼과 해당 입력을 처리하는 프로그램 사이에 토큰을 사용하여, 공격자의 직접적인 URL 사용이 동작하지 않도록 처리한다. 특히 중요한 기능에 대해서는 사용자 세션검증과 더불어 재인증을 유도한다.

#### 다. 코드예제

클라이언트로부터의 요청(request)에 대해서 정상적인 요청 여부인지를 검증하지 않고 처리하는 경우, 크로스사이트 요청 위조 공격에 쉽게 노출될 수 있다.

**안전하지 않은 코드의 예**

```text
// 어떤 형태의 요청이던지 기본적으로 CSRF 취약점을 가질 수 있다.
```

정상 요청 여부를 판단하기 위해 토큰을 이용한다. 사용자가 입력(신청) 페이지를 요청하면 임의의 토큰을 생성한 후 세션에 저장하고, 입력(신청) 페이지에 생성한 토큰을 HIDDEN 필드 항목의 값으로 설정한다. 입력(신청)을 처리하는 페이지에서는 입력(신청) 페이지에서 요청 파라미터로 전달 된 HIDDEN 필드의 토큰 값과 세션에 저장된 토큰 값을 비교하여 일치하는 경우에만 정상 요청으로 판단하여 입력(신청)이 처리될 수 있도록 한다.

**안전한 코드의 예 JAVA**

```java
// 입력화면이 요청되었을 때, 임의의 토큰을 생성한 후 세션에 저장한다.
session.setAttribute("SESSION_CSRF_TOKEN", UUID.randomUUID().toString());
// 입력화면에 임의의 토큰을 HIDDEN 필드항목의 값으로 설정해 서버로 전달되도록 한다.
<input type="hidden" name="param_csrf_token" value="$ {SESSION_CSRF_TOKEN }"/>

// 요청 파라미터와 세션에 저장된 토큰을 비교해서 일치하는 경우에만 요청을 처리한다.
String pToken = request.getParameter("param_csrf_token");
String sToken = (String)session.getAttribute("SESSION_CSRF_TOKEN");
if (pToken != null && pToken.equals(sToken) {
    // 일치하는 토큰이 존재하는 경우 -> 정상 처리
     ......
} else {
  // 토큰이 없거나 값이 일치하지 않는 경우 -> 오류 메시지 출력
     ......
}
```

AntiForgeryToken() 등을 이용하여 크로스사이트 요청 위조를 방지해야 한다.

**안전한 코드의 예 C#**

```csharp
@using (Html.BeginForm("PostTest","Home",FormMethod.Post,null))
{
       // AntiForgeryToken() 을 이용해 크로스사이트 요청 위조를 방지
      @Html.AntiForgeryToken()
      <input type="submit" value="Html PsBk Click" />
}
```

#### 라. 참고자료

- ① CWE-352 Cross-Site Request Forgery(CSRF), MITRE, http://cwe.mitre.org/data/definitions/352.html
- ② “Security Corner: Cross-Site Request Forgeries”, Chris Shiflett, http://shiflett.org/articles/cross-site-request-forgeries
- ③ Cross-Site_Request_Forgery_(CSRF), https://www.owasp.org/index.php/Cross-Site_Request_Forgery_(CSRF)
### 12. 서버사이드 요청 위조

#### 가. 개요

적절한 검증절차를 거치지 않은 사용자 입력 값을 서버간의 요청에 사용하여 악의적인 행위가 발생할 수 있는 보안약점이다.

외부에 노출된 웹 서버에 취약한 애플리케이션이 존재하는 경우 공격자는 URL 또는 요청문을 위조하여 접근통제를 우회하는 방식으로 비정상적인 동작을 유도하거나 신뢰된 네트워크에 있는 데이터를 획득할 수 있다.

#### 나. 보안대책

식별할 수 있는 범위 내에서 사용자의 입력 값을 다른 시스템의 서비스 호출에 사용하는 경우, 사용자의 입력 값을 화이트리스트 방식으로 필터링한다.

사용자가 지정하는 무작위의 URL을 받아들여야 한다면 내부의 URL을 블랙리스트로 지정하여 필터링 한다. 또한 동일한 내부 네트워크에 있더라도 기기 인증, 접근권한을 확인하여 요청이 이루어질 수 있도록 한다.

#### 다. 코드예제

다음 예제는 사용자로부터 입력받은 값의 검증 없이 웹페이지를 접속하도록 구현되어 있다. 이 때, 공격자는 URL을 조작하여 내부 서버에 질의 하게 하여 데이터를 획득할 수 있다.

참고 : 삽입 코드의 예

| 설명 | 삽입 코드의 예 |
|---|---|
| 내부망 중요 정보 획득 | • http://site_example.com/connect?url=http://192.168.0.45/member/list.json |
| 외부 접근 차단된 admin 페이지 접근 | • http://site_example.com/connect?url=http://192.168.0.45/admin |
| 도메인 체크를 우회하여 중요 정보 획득 | • http://site_example.com/connect?url=http://site_example.com:x@192.168.0.45/member/list.json |
| 단축 URL을 이용한 Filter 우회 | • http://site_example.com/connect?url=http://bit.ly/sdjk3kjhkl3 |
| 도메인을 사설IP로 설정해 중요정보 획득 | • http://site_example.com/connect?url=http://internal.site.com/member/list.json |
| 서버내 파일 열람 | • http://site_example.com/connect?url=http://attack/fileview.html |

**안전하지 않은 코드의 예 JAVA**

```java
 protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws
IOException {
         // 사용자 입력값(url)을 검증없이 사용하여 안전하지 않다.
         URL url = new URL(req.getParameter("url"));
         HttpURLConnection conn = (HttpURLConnection) url.openConnection();
 }
```

다음은 사전에 정의된 URL 목록을 맵(Map) 객체에 정의하고 키 값으로 입력받아 키에 매칭되는 URL만 사용할 수 있으므로 URL값을 임의로 조작할 수 없다

**안전한 코드의 예 JAVA**

```java
 public class Connect {
         // key, value 형식으로 URL의 리스트를 작성한다.
         private Map<String, URL> urlMap;
         protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws
IOException {
                   // 사용자에게 urlMap의 key를 입력받아 urlMap에서 URL값을 참조한다.
                   URL url = urlMap.get(req.getParameter("url"));
                   // urlMap에서 참조한 값으로 Connection을 만들어 접속한다.
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
         }
}
```

#### 라. 참고자료

- ① CWE-918: Server-Side Request Forgery (SSRF), MITRE, https://cwe.mitre.org/data/definitions/918.html
- ② Server Side Request Forgery, OWASP, https://owasp.org/www-community/attacks/Server_Side_Request_Forgery
### 13. HTTP 응답분할

#### 가. 개요

HTTP 요청에 들어 있는 파라미터(Parameter)가 HTTP 응답헤더에 포함되어 사용자에게 다시 전달될 때, 입력값에 CR(Carriage Return)이나 LF(Line Feed)와 같은 개행문자가 존재하면 HTTP 응답이 2개 이상으로 분리될 수 있다. 이 경우 공격자는 개행문자를 이용하여 첫 번째 응답을 종료시키고, 두 번째 응답에 악의적인 코드를 주입하여 XSS 및 캐시 훼손(Cache Poisoning) 공격 등을 수행할 수 있다.

#### 나. 보안대책

요청 파라미터의 값을 HTTP응답헤더(예를 들어, Set-Cookie 등)에 포함시킬 경우 CR, LF와 같은 개행문자를 제거한다.

#### 다. 코드예제

외부 입력값을 사용하여 반환되는 쿠키의 값을 설정하고 있다. 그런데, 공격자가 Wiley Hacker ￦r￦nHTTP/1.1 200 OK￦r￦n를 lastLogin의 값으로 설정할 경우, 응답이 분리되어 전달되며 분리된 응답 본문의 내용을 공격자가 마음대로 수정할 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
// 외부로부터 입력받은 값을 검증 없이 사용할 경우 안전하지 않다.
String lastLogin = request.getParameter("last_login");
if (lastLogin == null || "".equals(lastLogin)) {
    return;
}
// 쿠키는 Set-Cookie 응답헤더로 전달되므로 개행문자열 포함 여부 검증이 필요
Cookie c = new Cookie("LASTLOGIN", lastLogin);
c.setMaxAge(1000);
c.setSecure(true);
response.addCookie(c);
response.setContentType("text/html");
```

외부에서 입력되는 값에 대하여 null 여부를 체크하고, 응답이 여러 개로 나눠지는 것을 방지하기 위해 개행문자를 제거하고 응답헤더의 값으로 사용한다.

**안전한 코드의 예 JAVA**

```java
String lastLogin = request.getParameter("last_login");
if (lastLogin == null || "".equals(lastLogin)) {
    return;
}
// 외부 입력값에서 개행문자(￦r￦n)를 제거한 후 쿠키의 값으로 설정
lastLogin = lastLogin.replaceAll("[￦￦r￦￦n]", "");
Cookie c = new Cookie("LASTLOGIN", lastLogin);
c.setMaxAge(1000);
c.setSecure(true);
response.addCookie(c);
```

외부 입력값으로 반환되는 쿠키값을 설정하는 C#코드이다. 이는 응답이 분리되어 전달될 수 있으며 분리된 응답 본문의 내용을 공격자가 마음대로 수정할 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
// 외부 입력값을 검증없이 사용하는 것은 안전하지 않다.
string usrInput = Request.QueryString["ID"];
Response.AddHeader("foo", "bar" + usrInput);
```

개행문자를 모두 제거한 이후에 사용해야 한다.

**안전한 코드의 예 C#**

```csharp
ring usrInput = Request.QueryString["ID"];
// 개행문자를 제거 한 이후에 사용해야 한다.
ring validatedInput = usrInput.Replace("￦n", "").Replace("￦r","");
sponse.AddHeader("foo", "bar" + validatedInput);
```

#### 라. 참고자료

- ① CWE-113 HTTP Response Splitting, MITRE, http://cwe.mitre.org/data/definitions/113. html
- ② HTTP Response Splitting, OWASP, https://www.owasp.org/index.php/HTTP_Response_Splitting
### 14. 정수형 오버플로우

#### 가. 개요

정수형 오버플로우는 정수형 크기는 고정되어 있는데 저장 할 수 있는 범위를 넘어서, 크기보다 큰 값을 저장하려 할 때 실제 저장되는 값이 의도치 않게 아주 작은 수이거나 음수가 되어 프로그램이 예기치 않게 동작될 수 있다. 특히 반복문 제어, 메모리 할당, 메모리 복사 등을 위한 조건으로 사용자가 제공하는 입력값을 사용하고 그 과정에서 정수형 오버플로우가 발생하는 경우 보안상 문제를 유발 할 수 있다.

#### 나. 보안대책

언어/플랫폼별 정수타입의 범위를 확인하여 사용한다. 정수형 변수를 연산에 사용하는 경우, 결과 값의 범위를 체크하는 모듈을 사용한다. 특히 외부입력값을 동적 메모리 할당에 사용하는 경우, 변수 값이 적절한 범위 내에 존재하는 값인지 확인한다.

#### 다. 코드예제

다음의 예제는 외부의 입력(slf_msg_param_num)을 이용하여 동적으로 계산한 값을 배열의 크기(size)를 결정하는데 사용하고 있다. 만일 외부 입력으로부터 계산된 값(param_ct)이 오버 플로우에 의해 음수값이 되면, 배열의 크기가 음수가 되어 시스템에 문제가 발생할 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
String msg_str = "";
String tmp = request.getParameter("slf_msg_param_num");
tmp = StringUtil.isNullTrim(tmp);
if (tmp.equals("0")) {
   msg_str = PropertyUtil.getValue(msg_id);
} else {
  // 외부 입력값을 정수형으로 사용할 때 입력값의 크기를 검증하지 않고 사용
  int param_ct = Integer.parseInt(tmp);
  String[] strArr = new String[param_ct];
```

동적 메모리 할당을 위해 외부 입력값을 배열의 크기로 사용하는 경우 그 값이 음수가 아닌지 검사하는 작업이 필요하다.

**안전한 코드의 예 JAVA**

```java
String msg_str = "";
String tmp = request.getParameter("slf_msg_param_num");
tmp = StringUtil.isNullTrim(tmp);
if (tmp.equals("0")) {
       msg_str = PropertyUtil.getValue(msg_id);
} else {
// 외부 입력값을 정수형으로 사용할 때 입력값의 크기를 검증하고 사용
try {
       int param_ct = Integer.parseInt(tmp);
       if (param_ct < 0) {
          throw new Exception();
       }
       String[] strArr = new String[param_ct];
} catch(Exception e) {
       msg_str = "잘못된 입력(접근) 입니다.";
}
```

외부 입력값으로 배열의 접근할 경우, 입력값이 너무 클 때 음수가 되어 시스템에 문제가 발생 할 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
public static void Main(string[] args)
{
     // 외부 입력값을 사용할 때, 입력 값의 크기가 너무 클 경우 오버플로우 발생
     int usrNum = Int32.Parse(args[0]);
     string[] array = {"one", "two", "three", "four" };
     string num = array[usrNum];
}
```

checked 구문을 이용하여 오버플로우 발생 확인 및 처리를 해야한다.

**안전한 코드의 예 C#**

```csharp
public static void Main(string[] args)
{
  // checked 구문을 사용하여 오버플로우의 발생 여부 및 크기 확인
  try {
    int usrNum = checked(Int32.Parse(args[0]));
    string[] array = {"one", "two", "three", "four" };
    if(usrNum < 3)string num = array[usrNum];
  }
  catch (System.OverflowException e) { … }
}

                                  안전하지 않은 코드의 예 C

id main(int argc, char* argv[])

// 외부 입력값을 사용할 때, 입력 값의 크기가 너무 클 경우 오버플로우 발생
int usr_num = 0;
char* num_array[] = {“one”, “two”, “three”, “four” };
char* num = NULL;
usr_num = atoi(argv[1]);
num = num_array[usr_num];
}

                                    안전한 코드의 예 C

id main(int argc, char* argv[])

      // 외부 입력값을 사용할 때, 입력 값의 크기가 너무 클 경우 오버플로우 발생
int usr_num = 0;
 char* num_array[] = {“one”, “two”, “three”, “four” };
 char* num = NULL;
 usr_num = atoi(argv[1]);
 if (usr_num >= 0 && usr_num < 4) {
   num = num_array[usr_num];
}
  }
```

#### 라. 참고자료

- ① CWE-190 Integer Overflow, MITRE, http://cwe.mitre.org/data/definitions/190.html
- ② Enforce limits on integer values originating from tainted sources, CERT, http://www.securecoding.cert.org/confluence/display/c/INT04- C.+Enforce+limits+ on+integer+ values+originating+from+tainted+sources
- ③ Verify that all integer values are in range, CERT, http://www.securecoding.cert.org/confluence/display/c/INT08-C.+Verify+that+all+ integer+values+are+in+range
- ④ Integer overflow, OWASP, https://www.owasp.org/index.php/OWASP_Periodic_Table_of_Vulnerabilities_-_Integer_Overflow/Underflow
### 15. 보안기능 결정에 사용되는 부적절한 입력값

#### 가. 개요

응용프로그램이 외부 입력값에 대한 신뢰를 전제로 보호메커니즘을 사용하는 경우 공격자가 입력값을 조작할 수 있다면 보호메커니즘을 우회할 수 있게 된다.

개발자들이 흔히 쿠키, 환경변수 또는 히든필드와 같은 입력값이 조작될 수 없다고 가정 하지만 공격자는 다양한 방법으로 이러한 입력값들을 변경할 수 있고 조작된 내용은 탐지되지 않을 수 있다. 인증이나 인가와 같은 보안결정이 이런 입력값(쿠키, 환경변수, 히든필드 등)에 기반해 수행 되는 경우 공격자는 이런 입력값을 조작하여 응용프로그램의 보안을 우회할 수 있으므로 충분한 암호 화, 무결성 체크를 수행하고 이와 같은 메커니즘이 없는 경우엔 외부사용자에 의한 입력값을 신뢰해서는 안 된다.

#### 나. 보안대책

상태정보나 민감한 데이터 특히 사용자 세션정보와 같은 중요한 정보는 서버에 저장하고 보안확인 절차도 서버에서 실행한다. 보안설계관점에서 신뢰할 수 없는 입력값이 응용프로그램 내부로 들어올 수 있는 지점과 보안결정에 사용되는 입력값을 식별하고 제공되는 입력값에 의존할 필요가 없는 구조 로 변경할 수 있는지 검토한다.

#### 다. 코드예제

구입품목의 가격을 사용자 웹브라우저에서 처리하고 있어 이 값이 사용자에 의해 변경되는 경우 가격 (단가)정보가 의도하지 않은 값으로 할당될 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
 <input type="hidden" name="price" value="1000"/>
 <br/>품목 : HDTV
 <br/>수량 : <input type="hidden" name="quantity" />개
 <br/><input type="submit" value="구입" />
 ......

                             안전하지 않은 코드의 예 JAVA

try {
 // 서버가 보유하고 있는 가격(단가) 정보를 사용자 화면에서 받아서 처리
     price = request.getParameter("price");
     quantity = request.getParameter("quantity");
     total = Integer.parseInt(quantity) * Float.parseFloat(price);
} catch (Exception e) {
......
```

사용자 권한, 인증 여부 등 보안결정에 사용하는 값은 사용자 입력값을 사용하지 않고 서버 내부의 값을 활용한다. 또한 사용자 입력에 의존해야하는 값을 제외하고는 반드시 서버가 보유하고 있는 정보를 이용하여 처리한다.

**안전한 코드의 예 JAVA**

```java
<input type="hidden" name="price" value="1000"/>
<br/>품목 : HDTV
<br/>수량 : <input type="hidden" name="quantity" />개
<br/><input type="submit" value="구입" />
......
try {
     item = request.getParameter(“item”);
    // 가격이 아니라 item 항목을 가져와서 서버가 보유하고 있는 가격정보를 이용하여 전체 가격을
       계산
   price = productService.getPrice(item);
   quantity = request.getParameter("quantity");
   total = Integer.parseInt(quantity) * price;
} catch (Exception e) {
   ......
}
......
```

평문으로 사용자의 인증정보를 쿠키에 저장하고 있는 C# 예제코드이다.

**안전하지 않은 코드의 예 C#**

```csharp
HttpCookie cookie = new HttpCookie(“Authentificated”, “1”);
//평문으로 사용자의 인증정보를 쿠키에 저장한다.
Response.Cookies.Add(cookie);
```

중요한 정보를 쿠키에 저장시에는 암호화해서 사용하고, 되도록이면 해당정보는 서버의 세션에 저장하도록 한다.

**안전한 코드의 예 C#**

```csharp
// 사용자의 인증정보를 세션에 저장한다.
Session[“Authentificated”] = “1”;
```

아래 C 코드는 외부에서 가져온 서버 정보를 기반으로 연결을 진행한다. 사용자가 환경변수를 조작 하면 의도하지 않은 곳으로 연결을 진행할 수 있다. 예를 들어 온라인으로 제품 라이선스를 검증하는 경우, 인증 서버의 주소를 사용자가 변경하여 임의로 라이선스 검증을 통과할 수 있다.

**안전하지 않은 코드의 예 C**

```c
void SecurityDecision() {
    int sockfd = socket(PF_INET, SOCK_STREAM, 0);
    char* server_info = getenv(“server_addr”);
    // 외부에서 가져온 서버 정보를 그대로 사용한다.
    if( connect( sockfd, (struct sockaddr *)server_addr, sizeof(struct socketaddr) ) < 0 ) {
        return;
    }
    /* 라이선스 검증 코드 */
}
```

인증 서버의 정보를 환경 변수가 아닌 고정된 정보를 이용하여 연결을 진행한다.

**안전한 코드의 예 C#**

```csharp
void SecurityDecision() {
    int sockfd = socket(PF_INET, SOCK_STREAM, 0);
    struct sockaddr_in server_addr;
    memset( &server_ info, 0, sizeof(server_info));
    server_info.sin_family = AF_INET;
    server_info.sin_port = htons(5555);
    server_info.sin_addr.s_addr = inet_addr(“127.0.0.1”);
    // 고정된 서버 주소를 사용하여 연결을 진행한다.
    if( connect( sockfd, (struct sockaddr *)server_addr, sizeof(struct socketaddr) ) < 0 ) {
      return;
     }
    /* 라이선스 검증 코드 */
}
```

#### 라. 참고자료

- ① CWE-807 Reliance on Untrusted Inputs in a Security Decision, MITRE, http://cwe.mitre.org/data/definitions/807.html
- ② Do not trust the values of environment variables, CERT, http://www.securecoding.cert.org/confluence/display/java/ENV02-J.+Do+not+trust+ the+values+of+environment+ variables
- ③ Session Management, OWASP, https://www.owasp.org/index.php/Session_Management_Cheat_Sheet
### 16. 메모리 버퍼 오버플로우

#### 가. 개요

메모리 버퍼 오버플로우 보안약점은 연속된 메모리 공간을 사용하는 프로그램에서 할당된 메모리의 범위를 넘어선 위치에 자료를 읽거나 쓰려고 할 때 발생한다. 메모리 버퍼 오버플로우는 프로그램의 오동작을 유발시키거나, 악의적인 코드를 실행시킴으로써 공격자 프로그램을 통제할 수 있는 권한을 획득하게 한다.

메모리 버퍼 오버플로우에는 스택 메모리 버퍼 오버플로우와 힙 메모리 버퍼 오버플로우가 있다.

다음은 스택 메모리 버퍼 오버플로우를 발생시키는 코드이다.

void foo() { int num = 10; char message[40]; gets(message);5: }

정상적인 프로그램의 실행은 다음과 같은 메모리 구조를 가지며, 함수 foo()의 스택 공간 끝에는 복귀 주소가 보관된다.

gets()와 같은 함수는 문자열을 크기와 상관없이 연속된 기억공간에 저장시키는 함수이므로, 공격자는 정상적인 문자열 대신 공격코드를 입력하고 스택의 시작주소 0xAABB를 반복 입력한다. 이 경우 다음과 같은 메모리 구조에 의해 프로그램은 정상 주소로 복귀하는 대신 공격코드의 시작주소로 복귀하여 공격코드를 수행하게 된다.

#### 나. 보안대책

프로그램 상에서 메모리 버퍼를 사용할 경우 적절한 버퍼의 크기를 설정하고, 설정된 범위의 메모리 내에서 올바르게 읽거나 쓸 수 있게 통제하여야 한다. 특히, 문자열 저장 시 널(Null) 문자로 종료하지 않으면 의도하지 않은 결과를 가져오게 되므로 널(Null) 문자를 버퍼 범위 내에 삽입하여 널(Null) 문자로 종료되도록 해야 한다.

#### 다. 코드예제

다음 코드는 포인터 구조체의 개별 필드에 특정 문자열을 복사하는 프로그램이다. 잘못 계산된 데이터 크기 sizeof(cv_struct)로 인해 프로그램은 연속된 메모리 공간인 포인터 y를 덮어쓰는 버퍼 오버플로우를 발생시킨다. 또한 프로그램은 복사된 문자열에 대해 종료 문자를 첨가시키지 않았기 때문에 문자열의 참조 시 잘못된 결과를 가져올 수 있다.

**안전하지 않은 코드의 예 C**

```c
typedef struct _charvoid {
    char x[16];
    void * y;
    void * z;
} charvoid
void badCode() {
     charvoid cv_struct
    cv_struct.y = (void *) SRC_STR;
    printLine((char *) cv_struct.y);

    /* sizeof(cv_struct)의 사용으로 포인터 y에 덮어쓰기 발생 */
    memcpy(cv_struct.x, SRC_STR, sizeof(cv_struct));
    printLine((char *) cv_struct.x);
    printLine((char *) cv_struct.y);15:
}
```

안전한 코드가 되기 위해서는 첫째, 문자열 복사는 구조체 내의 필드값 x에 한정되는 것이므로 정확한 문자열 계산인 sizeof(cv_struct.x)으로 허용된 범위의 인덱스만을 사용하도록 수정한다. 둘째, 복사된 문자열은 올바른 널(Null) 정보를 가져야 하므로 복사된 값을 가진 cv_ struct.x 배열의 가장 마지막 인덱스를 계산하여 널(Null) 문자를 패딩해야 한다.

**안전한 코드의 예 C**

```c
typedef struct _charvoid {
     char x[16];
     void * y;
     void * z;
} charvoid

static void goodCode() {
     charvoid cv_struct
     cv_struct.y = (void *) SRC_STR;
     printLine((char *) cv_struct.y);

    /* sizeof(cv_struct.x)로 변경하여 포인터 y의 덮어쓰기를 방지함 */
    memcpy(cv_struct.x, SRC_STR, sizeof(cv_struct.x));

    /* 문자열 종료를 위해 널 문자를 삽입함 */
    cv_struct.x[(sizeof(cv_struct.x)/sizeof(char))-1] = '￦0';
    printLine((char *) cv_struct.x);
    printLine((char *) cv_struct.y);
}
```

#### 라. 참고자료

- ① CWE-119 Improper Restriction of Operations within the Bounds of a Memory Buffer, MITRE, http://cwe.mitre.org/data/definitions/119.html
- ② Buffer overflow attack, OWASP, https://www.owasp.org/index.php/Buffer_overflow_ attack
### 17. 포맷 스트링 삽입

#### 가. 개요

외부로부터 입력된 값을 검증하지 않고 입·출력 함수의 포맷 문자열로 그대로 사용하는 경우 발생할 수 있는 보안약점이다. 공격자는 포맷 문자열을 이용하여 취약한 프로세스를 공격하거나 메모리 내용을 읽거나 쓸 수 있다. 그 결과, 공격자는 취약한 프로세스의 권한을 취득하여 임의의 코드를 실행할 수 있다.

#### 나. 보안대책

printf(), snprintf() 등 포맷 문자열을 사용하는 함수를 사용할 때는 사용자 입력값을 직접적으로 포맷 문자열로 사용하거나 포맷 문자열 생성에 포함시키지 않는다. 포맷문자열을 사용하는 함수에 사용자 입력값을 사용할 때는 사용자가 포맷 스트링을 변경할 수 있는 구조로 쓰지 않는다. 특히, %n, %hn은 공격자가 이를 이용해 특정 메모리 위치에 특정값을 변경할 수 있으므로 포맷 스트링 매개변수로 사용하지 않는다. 사용자 입력값을 포맷 문자열을 사용하는 함수에 사용할 때는 가능하면 %s 포맷 문자열을 지정하고, 사용자 입력값은 2번째 이후의 파라미터로 사용한다.

#### 다. 코드예제

포맷 스트링 보안약점은 C 언어에 국한된 것은 아니다. 아래 예제 코드는 입력 자료의 유효성을 검증하지 않은 Java 프로그램에서도 발생할 수 있음을 보여준다. 이 프로그램에서 공격자는 %1$tm, %1$te, 또는 %1$tY과 같은 문자열을 입력하여 포맷 문자열에 포함시킴으로써, 실제 유효기간 validDate가 출력되도록 할 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
// 외부 입력값에 포맷 문자열 포함 여부를 확인하지 않고 포맷 문자열 출력에 값으로 사용
// args[0]의 값으로 “%1$tY-%1$tm-%1$te"를 전달하면 시스템에서 가지고 있는 날짜
   (2014-10-14) 정보가 노출
import java.util.Calendar
......
public static void main(String[] args) {

                                   안전하지 않은 코드의 예 C#

        Calendar validDate = Calendar.getInstance();
       validDate.set(2014, Calendar.OCTOBER, 14);

       System.out.printf( args[0] + " did not match! HINT: It was issued on %1$terd
     of some month", validate);
 }
```

사용자로부터 입력 받은 문자열을 포맷 문자열에 직접 포함시키지 않고, %s 포맷 문자열을 사용함으로써 정보유출을 방지한다.

**안전한 코드의 예 JAVA**

```java
// 외부 입력값이 포맷 문자열 출력에 사용되지 않도록 수정
import java.util.Calendar
          :
public static void main(String[] args) {
      Calendar validDate = Calendar.getInstance();
     validDate.set(2014, Calendar.OCTOBER, 14);
     System.out.printf("%s did not match! HINT: It was issued on %2$terd of some
    month", args[0], validate);
}
```

이 예제의 msg는 신뢰할 수 없는 사용자 입력을 포함하고 있고 fprintf() 호출에서 포맷문자열 인자로 전달되기 때문에 포맷스트링 삽입에 취약하다.

**안전하지 않은 코드의 예 C**

```c
void incorrect_password(const char *user) {
      static const char msg_format[] = "%s cannot be authenticated.￦n";
      size_t len = strlen(user) + sizeof(msg_format);
      char *msg = (char *)malloc(len);
      if (msg == NULL) {

                                     안전하지 않은 코드의 예 C

           /* 오류 처리 */
      }
      int ret = snprintf(msg, len, msg_format, user);
            if (ret < 0 || ret >= len) {
           /* 오류 처리 */
      }
//
     fprintf(stderr, msg);
     free(msg);
     msg = NULL;
}
```

이 예제는 fprintf() 대신에 fputs()를 사용하여, msg를 포맷문자열처럼 취급하지 않고 그대로 stderr로 출력한다.

**안전한 코드의 예 C**

```c
void incorrect_password(const char *user) {
     static const char msg_format[] = "%s cannot be authenticated.￦n";
      size_t len = strlen(user) + sizeof(msg_format);
      char *msg = (char *)malloc(len);
      if (msg == NULL) {
             /* 오류 처리 */
       }
      int ret = snprintf(msg, len, msg_format, user);
      if (ret < 0 || ret >= len) {
     /* 오류 처리 */
     }
if (fputs(msg, stderr) == EOF) {
     /* 오류 처리 */
       }
     free(msg);
     msg = NULL;
}
```

#### 라. 참고자료

- ① CWE-134 Uncontrolled Format String, MITRE, http://cwe.mitre.org/data/definitions/134.html
- ② Exclude user input from format strings, CERT, http://www.securecoding.cert.org/confluence/display/c/FIO30-C.+Exclude+user+input+from+format+stringsb
- ③ Use valid format strings, CERT, http://www.securecoding.cert.org/confluence/display/c/FIO47-C.+Use+valid+format+strings
- ④ Format string attack, OWASP, https://www.owasp.org/index.php/Format_string_attack
## 제2절 보안기능

보안기능(인증, 접근제어, 기밀성, 암호화, 권한관리 등)을 부적절하게 구현 시 발생할 수 있는 보안 약점으로 적절한 인증 없는 중요기능 허용, 부적절한 인가 등이 포함된다.

### 1. 적절한 인증 없는 중요기능 허용

#### 가. 개요

적절한 인증과정이 없이 중요정보(계좌이체 정보, 개인정보 등)를 열람(또는 변경)할 때 발생하는 보안약점이다.

#### 나. 보안대책

클라이언트의 보안검사를 우회하여 서버에 접근하지 못하도록 설계하고 중요한 정보가 있는 페이지는 재인증을 적용(은행 계좌이체 등)한다. 또한 안전하다고 검증된 라이브러리나 프레임워크 (OpenSSL 이나 ESAPI의 보안기능 등)를 사용하는 것이 중요하다.

#### 다. 코드예제

회원정보 수정 시 수정을 요청한 사용자와 로그인한 사용자의 일치 여부를 확인하지 않고 처리하고 있다.

**안전하지 않은 코드의 예 JAVA**

```java
@RequestMapping(value = "/modify.do", method = RequestMethod.POST)
public ModelAndView memberModifyProcess(@ModelAttribute("MemberModel")
MemberModel memberModel, BindingResult result, HttpServletRequest request,
HttpSession session) {
  ModelAndView mav = new ModelAndView();
  //1. 로그인한 사용자를 불러온다.
 String userId = (String) session.getAttribute("userId");

                               안전하지 않은 코드의 예 JAVA

   String passwd = request.getParameter("oldUserPw");
 ...
   //2. 실제 수정하는 사용자와 일치 여부를 확인하지 않고, 회원정보를 수정하여 안전하지 않다.
   if (service.modifyMember(memberModel)) {
      mav.setViewName("redirect:/board/list.do");
      session.setAttribute("userName", memberModel.getUserName());
      return mav;
   } else {
     mav.addObject("errCode", 2);
     mav.setViewName("/board/member_modify");
     return mav;
   }
 }
```

로그인한 사용자와 요청한 사용자의 일치 여부를 확인한 후 회원정보를 수정하도록 한다.

**안전한 코드의 예 JAVA**

```java
@RequestMapping(value = "/modify.do", method = RequestMethod.POST)
public ModelAndView memberModifyProcess(@ModelAttribute("MemberModel")
  MemberModel memberModel, BindingResult result, HttpServletRequest request,
   HttpSession session) {
   ModelAndView mav = new ModelAndView();

      //1. 로그인한 사용자를 불러온다.
      String userId = (String) session.getAttribute("userId");
      String passwd = request.getParameter("oldUserPw");

      //2. 회원정보를 실제 수정하는 사용자와 로그인 사용자와 동일한지 확인한다.
      String requestUser = memberModel.getUserId();
      if (userId != null && requestUser != null && !userId.equals(requestUser)) {
           mav.addObject("errCode", 1);
           mav.addObject("member", memberModel);
          mav.setViewName("/board/member_modify");
           return mav;
      }
...

                              안전한 코드의 예 JAVA

   //3. 동일한 경우에만 회원정보를 수정해야 안전하다.
   if (service.modifyMember(memberModel)) {
...
```

사용자 자격인증 없이 로그인 기능을 수행하는 C# 코드의 예제이다.

**안전하지 않은 코드의 예 C#**

```csharp
protected void LoginButton_Click(object sender, EventArgs e) {
// 사용자의 자격인증 과정이 없이 로그인 기능을 수행한다.
   FormsAuthentication.RedirectFromLoginPage(UserName.Text,
 RememberMe.Checked);
}
```

사용자의 자격인증 후 로그인 기능을 수행해야 한다.

**안전한 코드의 예 C#**

```csharp
protected void LoginButton_Click(object sender, EventArgs e) {
// 사용자의 자격인증 과정을 수행한다.
   if(Membership.ValidateUser(UserName.Text, Password.Text)) {
       FormsAuthentication.RedirectFromLoginPage(UserName.Text,
RememberMe.Checked);
   }
}
```

#### 라. 참고자료

- ① CWE-306 Missing Authentication for Critical Function, MITRE, http://cwe.mitre.org/data/definitions/306.html
- ② Access Control, OWASP, https://www.owasp.org/index.php/Access_Control_Cheat_ Sheet
### 2. 부적절한 인가

#### 가. 개요

프로그램이 모든 가능한 실행경로에 대해서 접근제어를 검사하지 않거나 불완전하게 검사하는 경우, 공격자는 접근 가능한 실행경로로 정보를 유출할 수 있다.

#### 나. 보안대책

응용프로그램이 제공하는 정보와 기능을 역할에 따라 배분함으로써 공격자에게 노출되는 공격 노출면6 (Attack Surface)을 최소화하고 사용자의 권한에 따른 ACL(Access Control List)을 관리한다. 프레임워크를 사용해서 취약점을 피할 수도 있는데 예를 들면, JAAS Authorization Framework나 OWASP ESAPI Access Control 등을 인증 프레임워크로 사용 가능하다.

#### 다. 코드예제

아래의 코드는 사용자 입력값에 따라 삭제작업을 수행하고 있으며, 사용자의 권한 확인을 위한 별도의 통제가 적용되지 않고 있다.

**안전하지 않은 코드의 예 JAVA**

```java
private BoardDao boardDao;
String action = request.getParameter("action");
String contentId = request.getParameter("contentId");
// 요청을 하는 사용자의 delete 작원 권한 확인 없이 수행하고 있어 안전하지 않다.
      if (action != null && action.equals("delete")) {
         boardDao.delete(contentId);
  }
```

> <sup>6</sup> OSSTMM 3 Defines Attack Surface as "The lack of specific separations and functional controls that exist for that vector"

아래의 코드처럼 세션에 저장된 사용자 정보로 해당 사용자가 삭제작업을 수행할 권한이 있는지 확인한 뒤 권한이 있는 경우에만 수행하도록 해야 한다.

**안전한 코드의 예 JAVA**

```java
private BoardDao boardDao;
String action = request.getParameter("action");
String contentId = request.getParameter("contentId");
    // 세션에 저장된 사용자 정보를 얻어온다.
    User user= (User)session.getAttribute("user");
   // 사용자정보에서 해당 사용자가 delete작업의 권한이 있는지 확인한 뒤 삭제 작업을 수행한다.
   if (action != null && action.equals("delete") &&
  checkAccessControlList(user,action)) {
         boardDao.delete(contenId);
   }
}
```

운영자 권한 검사 없이 컨트롤러와 내부의 개별액션에 접근이 가능한 C# 코드이다.

**안전하지 않은 코드의 예 C#**

```csharp
// 운영자 권한 검사 없이 컨트롤러와 내부의 개별 액션에 접근 가능
public class AdministrationController : Controller
{
…
}
```

운영자 권한 검사 후에 개별 액션에 접근해야 한다.

**안전한 코드의 예 C#**

```csharp
// 운영자 권한 검사 후 개별 액션에 접근
[Authorize(Roles = "Administrator")]
public class AdministrationController : Controller
{
…
}
```

사용자 자격인증 없이 LDAP 검색을 시도하는 C코드의 예제이다.

**안전하지 않은 코드의 예 C**

```c
#define FIND_DN "uid=han,ou=staff,dc=example,dc=com"
int searchData2LDAP(LDAP *ld, char *username) {
    unsigned long rc;
    char filter[20];
    LDAPMessage *result;
    snprintf(filter, sizeof(filter),"(name=%s)",username);
    // 사용자의 인증 없이 LDAP 검색을 시도한다.
    rc = ldap_search_ext_s(ld, FIND_DN, LDAP_SCOPE_BASE, filter, NULL, 0,
      NULL, NULL, LDAP_NO_LIMIT, LDAP_NO_LIMIT, &result);
    return rc;
}
```

사용자의 자격인증 및 로그인 정보와 일치하는지 검사 후 LDAP 검색을 진행해야 한다.

**안전한 코드의 예 C**

```c
#define FIND_DN "uid=han,ou=staff,dc=example,dc=com"
  int searchData2LDAP(LDAP *ld, char *username, char *password) {
    unsigned long rc;
char filter[20];
  LDAPMessage *result
    // username 을 인증한다.
    if ( ldap_simple_bind_s(ld, username, password) != LDAP_SUCCESS ) {
      printf("authorization error");
     return(FAIL);
    }
    // username 이 로그인 정보와 일치하는지 검사한다.
    if ( strcmp(username,getLoginName()) != 0 ) {
    printf("Login error");
    return(FAIL);
}
    snprintf(filter, sizeof(filter), "(name=%s)", username);

                                 안전한 코드의 예 C

    rc = ldap_search_ext_s(ld, FIND_DN, LDAP_SCOPE_BASE, filter, NULL, 0,
     NULL, NULL, LDAP_NO_LIMIT, LDAP_NO_LIMIT, &result);
    return rc;
}
```

#### 라. 참고자료

- ① CWE-285 Improper Authorization, MITRE, http://cwe.mitre.org/data/definitions/285. html
- ② Access Control, OWASP, https://www.owasp.org/index.php/Access_Control_Cheat_ Sheet
### 3. 중요한 자원에 대한 잘못된 권한 설정

#### 가. 개요

SW가 중요한 보안관련 자원에 대하여 읽기 또는 수정하기 권한을 의도하지 않게 허가할 경우, 권한을 갖지 않은 사용자가 해당 자원을 사용하게 된다.

#### 나. 보안대책

설정파일, 실행파일, 라이브러리 등은 SW 관리자에 의해서만 읽고 쓰기가 가능하도록 설정하고 설정파일과 같이 중요한 자원을 사용하는 경우, 허가 받지 않은 사용자가 중요한 자원에 접근 가능 한지 검사한다.

#### 다. 코드예제

“/home/setup/system.ini” 파일에 대해 모든 사용자가 읽고, 쓰고, 실행할 수 있도록 권한을 부여하고 있다.

- setExecutable(p1, p2) : 첫 번째 파라미터의 true/false 값에 따라 실행가능 여부를 결정한다. 두 번째 파라미터가 true 일 경우 소유자만 실행 권한을 가지며, false 일 경우 모든 사용자가 실행 권한을 가진다.
- setReadable(p1, p2) : 첫 번째 파라미터의 true/false 값에 따라 읽기가능 여부를 결정한다. 두 번째 파라미터가 true 일 경우 소유자만 읽기권한을 가지며, false 일 경우 모든 사용자가 읽기 권한을 가진다.
- setWritable(p1, p2) : 첫 번째 파라미터의 true/false 값에 따라 쓰기가능 여부를 결정한다. 두 번째 파라미터가 true 일 경우 소유자만 쓰기권한을 가지며, false 일 경우 모든 사용자가 쓰기 권한을 가진다.
**안전하지 않은 코드의 예 JAVA**

```java
File file = new File("/home/setup/system.ini");
// 모든 사용자에게 실행 권한을 허용하여 안전하지 않다.
file.setExecutable(true, false);
// 모든 사용자에게 읽기 권한을 허용하여 안전하지 않다.
file.setReadable(true, false);
// 모든 사용자에게 쓰기 권한을 허용하여 안전하지 않다.
file.setWritable(true, false);
```

파일에 대해서는 최소권한을 할당해야 한다. 즉 해당 파일의 소유자에게만 읽기 권한을 부여한다.

- setExecutable(p1) : 파라미터의 true/false 값에 따라 소유자의 실행권한 여부를 결정한다.
- setReadable(p1) : 파라미터의 true/false 값에 따라 소유자의 읽기권한 여부를 결정한다.
- setWritable(p1) : 파라미터의 true/false 값에 따라 소유자의 쓰기권한 여부를 결정한다.
**안전한 코드의 예 JAVA**

```java
File file = new File("/home/setup/system.ini");
// 소유자에게 실행 권한을 금지하였다.
file.setExecutable(false);
// 소유자에게 읽기 권한을 허용하였다.
file.setReadable(true);
// 소유자에게 쓰기 권한을 금지하였다.
file.setWritable(false);
```

아래의 C# 코드는 모든 사용자에게 파일의 권한을 부여하고 있다.

**안전하지 않은 코드의 예 C#**

```csharp
public static void AddDirectorySecurity(string FileName)
{
     // 디렉토리 정보 객체 생성
    DirectoryInfo dInfo = new DirectoryInfo(FileName);
    DirectorySecurity dSecurity = dInfo.GetAccessControl();

    // 모든 사용자에게 권한 부여.
    dSecurity.AddAccessRule(new FileSystemAccessRule("everyone",
    FileSystemRights.FullControl,
    InheritanceFlags.ObjectInherit | InheritanceFlags.ContainerInherit,
    PropagationFlags.NoPropagateInherit, AccessControlType.Allow));
    dInfo.SetAccessControl(dSecurity);
}
```

적절한 권한을 파일에 설정해야 한다.

**안전한 코드의 예 C#**

```csharp
public static void AddDirectorySecurity(string FileName, string Account,
     FileSystemRights Rights, AccessControlType ControlType)
{
     // 디렉토리 정보 객체 생성
     DirectoryInfo dInfo = new DirectoryInfo(FileName);
     DirectorySecurity dSecurity = dInfo.GetAccessControl();

     // FileSystemAccessRule 에 권한 설정
    dSecurity.AddAccessRule(new FileSystemAccessRule(Account,
                                                              Rights,
                                                              ControlType));
       dInfo.SetAccessControl(dSecurity);
}
```

모든 사용자에게 권한을 부여하는 C코드의 예제이다.

**안전하지 않은 코드의 예 C**

```c
// 모든 사용자가 읽기/쓰기 권한을 갖게 된다.
umask(0);
FILE *out = fopen("file_name", "w");
if(out) {
  fprintf(out, "secure code￦n");
  fclose(out);
```

umask()를 사용하여 권한 설정을 할 때, 올바른 권한을 설정해야 합니다.

**안전한 코드의 예 C**

```c
// 유저 외에는 아무런 권한을 주지 않는다.
umask(077);
FILE *out = fopen("file_name", "w");
if(out) {
  fprintf(out, "secure code￦n");
  fclose(out);
```

#### 라. 참고자료

- ① CWE-732 Incorrect Permission Assignment for Critical Resource, MITRE, http://cwe.mitre.org/data/definitions/732.html
- ② Create files with appropriate access permissions, CERT, http://www.securecoding.cert.org/confluence/display/c/FIO06-C.+Create+files+with+appropriate+access+permissions
### 4. 취약한 암호화 알고리즘 사용

#### 가. 개요

SW 개발자들은 환경설정 파일에 저장된 패스워드를 보호하기 위하여 간단한 인코딩 함수를 이용하여 패스워드를 감추는 방법을 사용하기도 한다. 그렇지만 base64와 같은 지나치게 간단한 인코딩 함수로는 패스워드를 제대로 보호할 수 없다.

정보보호 측면에서 취약하거나 위험한 암호화 알고리즘을 사용해서는 안 된다. 표준화되지 않은 암호화 알고리즘을 사용하는 것은 공격자가 알고리즘을 분석하여 무력화시킬 수 있는 가능성을 높일 수도 있다. 몇몇 오래된 암호화 알고리즘의 경우는 컴퓨터의 성능이 향상됨에 따라 취약해지기도 해서, 예전에는 해독하는데 몇 십 억년이 걸릴 것이라고 예상되던 알고리즘이 며칠이나 몇 시간 내에 해독되기도 한다. RC2, RC4, RC5, RC6, MD4, MD5, SHA1, DES 알고리즘이 여기에 해당된다.

#### 나. 보안대책

자신만의 암호화 알고리즘을 개발하는 것은 위험하며, 학계 및 업계에서 이미 검증된 표준화된 알고리즘을 사용한다. 기존에 취약하다고 알려진 DES, RC5등의 암호알고리즘을 대 신하여, 3DES, AES, SEED 등의 안전한 암호알고리즘으로 대체하여 사용한다. 또한, 업무관련 내용, 개인정보 등에 대한 암호 알고리즘 적용 시, IT보안인증 사무국이 안전성을 확인한 검증필 암호모듈을 사용해야한다.

참고 : 안전한 암호알고리즘 및 키 길이

| 분류 | | 보호함수 목록 |
|---|---|---|
| 최소 안전성 수준 | | • 112비트 |
| 블록암호 | | • ARIA(키 길이 : 128/192/256),<br>• SEED(키 길이 : 128) |
| 블록암호 운영모드 | 기밀성 | • ECD, CBC, CFB, OFB, CTR |
| | 기밀성/인증 | • CCM, GCM |
| 해쉬함수 | | • SHA-224/256/384/512 |
| 메시지 인증코드 | 해쉬함수기반 | • HMAC |
| | 블록기반 | • CMAC, GMAC |
| 난수발생기 | 해쉬함수/HMAC 기반 | • HASH_DRBG, HMAC_DRBG |
| | 블록기반 | • CTR_DRBG |
| 공개키 암호 | | • RSAES<br>&nbsp;&nbsp;- (공개키 길이) 2048, 3072<br>&nbsp;&nbsp;- RSA-OAEP에서 사용되는 해쉬함수 : SHA-224/256 |
| 전자서명 | | • RSA-PSS, KCDSA, ECDSA, EC-KCDSA |
| 키 설정 방식 | | • DH, ECDH |

| 보호함수 | | 보호함수 파라미터 |
|---|---|---|
| 시스템 파라미터 | RSA-PSS | • (공개키 길이) 2048, 3072 |
| | KCDSA, DH | • (공개키 길이, 개인키 길이)<br>• (2048, 224), (2048, 256) |
| | ECDSA, EC-KCDSA, ECDH | • (FIPS) B-233, B-283<br>• (FIPS) K-233, K-283<br>• (FIPS) P-224, P-256 |

#### 다. 코드예제

다음 예제는 취약한 DES 알고리즘으로 암호화하고 있다.

**안전하지 않은 코드의 예 JAVA**

```java
import java.security.*;
import javax.crypto.Cipher;
import javax.crypto.NoSuchPaddingException;
public class CryptoUtils {
    public byte[] encrypt(byte[] msg, Key k) {
        byte[] rslt = null;
        try {
// 키 길이가 짧아 취약함 암호와 알고리즘인 DES를 사용하여 안전하지 않다.
            Cipher c = Cipher.getInstance("DES");
            c.init(Cipher.ENCRYPT_MODE, k);
            rslt = c.update(msg);
        }
```

아래 코드처럼 안전하다고 알려진 AES 알고리즘 등을 적용해야 한다.

**안전한 코드의 예 JAVA**

```java
import java.security.*;
import javax.crypto.Cipher;
import javax.crypto.NoSuchPaddingException;

public class CryptoUtils {
   public byte[] encrypt(byte[] msg, Key k) {
        byte[] rslt = null;
        try {
// 키 길이가 길어 강력한 알고리즘인 AES를 사용하여 안전하다.
             Cipher c = Cipher.getInstance("AES/CBC/PKCS5Padding");
             c.init(Cipher.ENCRYPT_MODE, k);
             rslt = c.update(msg);
        }
```

다음 예제는 취약한 DES 알고리즘을 사용하고 있다.

**안전하지 않은 코드의 예 C#**

```csharp
static string Enc(string input) {
// 키 길이가 짧아 취약함 암호와 알고리즘인 DES를 사용하여 안전하지 않다.
var des = new DESCryptoServiceProvider();
...
}
```

아래 코드처럼 안전하다고 알려진 AES 알고리즘 등을 적용해야 한다.

**안전한 코드의 예 C#**

```csharp
 static string Enc(string input) {
// 키 길이가 길어 강력한 알고리즘인 AES를 사용하여 안전하다.
    var des = new AesCryptoServiceProvider();
    ...
   }
```

다음 예제는 취약한 DES 알고리즘을 사용하고 있는 C 코드이다.

**안전하지 않은 코드의 예 C**

```c
EVP_CIPHER_CTX ctx;
EVP_CIPHER_CTX_init(&ctx);
// 취약한 DES 알고리즘을 사용한다.
EVP_EncryptInit(&ctx, EVP_des_ecb(), NULL, NULL);
```

안전하다고 알려진 AES 알고리즘을 사용하도록 한다.

**안전한 코드의 예 C**

```c
EVP_CIPHER_CTX ctx;
EVP_CIPHER_CTX_init(&ctx);
// 안전한 AES 알고리즘을 사용한다.
EVP_EncryptInit(&ctx, EVP_aes_128_cbc(), key, iv);
```

#### 라. 참고자료

- ① CWE-327 Use of a Broken or Riscky Cryptographic Algorithm, MITRE, http://cwe.mitre.org/data/definitions/327.html
- ② Do not use insecure or weak cryptographic algorithms, CERT, http://www.securecoding.cert.org/confluence/display/java/MSC61-J.+Do+not+use+insecure+or+weak+cryptographic+algorithms?focusedCommentId=186843241#comment-186843241
- ③ Cryptanalysis, OWASP, https://www.owasp.org/index.php/Cryptanalysis
### 5. 암호화되지 않은 중요정보

#### 가. 개요

사용자 또는 시스템의 중요정보가 포함된 데이터를 평문으로 송·수신 또는 저장할 때 인가되지 않은 사용자에게 민감한 정보가 노출될 수 있는 보안약점이다.

#### 나. 보안대책

개인정보(주민등록번호, 여권번호 등), 금융정보(카드번호, 계좌번호 등), 패스워드 등 중요정보를 통신채널로 전송하거나 저장할 때는 반드시 암호화 과정을 거쳐야 한다. 필요한 경우 SSL 또는 HTTPS 등과 같은 암호채널을 사용해야 하며, HTTPS와 같은 보안 채녈을 사용하여 브라우저 쿠키에 중요 데이터를 저장하는 경우, 쿠키객체에 보안속성을 반드시 설정하여 중요정보의 노출을 방지한다. 중요정보를 읽거나 쓸 경우에 권한인증 등으로 적합한 사용자가 중요정보에 접근하도록 해야 한다.

#### 다. 코드예제

- 중요정보 평문저장
아래 예제는 인증을 통과한 사용자의 패스워드 정보가 평문으로 DB에 저장된다.

**안전하지 않은 코드의 예 JAVA**

```java
```

String id = request.getParameter("id"); // 외부값에 의해 패스워드 정보를 얻고 있다. String pwd = request.getParameter("pwd"); ...... String sql = " insert into customer(id, pwd, name, ssn, zipcode, addr)" + " values (?, ?, ?, ?, ?, ?)"; PreparedStatement stmt = con.prepareStatement(sql); stmt.setString(1, id); stmt.setString(2, pwd); ...... // 입력받은 패스워드가 평문으로 DB에 저장되어 안전하지 않다. stmt.executeUpdate();

다음 예제는 패스워드 등 중요 데이터를 해쉬값으로 변환하여 저장하고 있다.

**안전한 코드의 예 JAVA**

```java
String id = request.getParameter("id");
// 외부값에 의해 패스워드 정보를 얻고 있다.
String pwd = request.getParameter("pwd");
// 패스워드를 솔트값을 포함하여 SHA-256 해쉬로 변경하여 안전하게 저장한다.
MessageDigest md = MessageDigest.getInstance("SHA-256");
md.reset();
md.update(salt);
byte[] hashInBytes = md.digest(pwd.getBytes());
StringBuilder sb = new StringBuilder();
        for (byte b : hashInBytes) {
           sb.append(String.format("%02x", b));
        }
pwd = sb.toString();
......
String sql = " insert into customer(id, pwd, name, ssn, zipcode, addr)"
             + " values (?, ?, ?, ?, ?, ?)";
PreparedStatement stmt = con.prepareStatement(sql);
stmt.setString(1, id);
stmt.setString(2, pwd);
......
stmt.executeUpdate();
```

다음은 사용자의 패스워드를 평문으로 저장해 놓고 출력하는 C# 코드의 예제이다.

**안전하지 않은 코드의 예 C#**

```csharp
 namespace Security
 {
   public class FindPassword : System.Web.UI.Page
   {
     protected void Page_Load(object sender, EventArgs e)
     {
        var userId = "tmp";
        MembershipUser user = Membership.GetUser(userId);

                                 안전하지 않은 코드의 예 C#

            if (user != null)
            {
                var password = user.GetPassword();
                Response.Write(password);
            }
            else
            {
                Response.Write("the given userId is not valid");
            }
        }
    }
}
```

패스워드는 암호화 하여 저장해야 하며, 출력하지 않도록 한다.

**안전한 코드의 예 C#**

```csharp
namespace Security
{
  public class FindPassword : System.Web.UI.Page
  {
    protected void Page_Load(object sender, EventArgs e)
    {
       var userId = "tmp";
        MembershipUser user = Membership.GetUser(userId);
        if (user != null)
        {
            var encrypetedPassword = user.GetPassword();
            SecureFindPasswordFunction();
        }
        else
        {
            Response.Write("the given userId is not valid");
        }
    }
  }
}
```

- 중요정보 평문전송
아래 예제는 패스워드를 암호화하지 않고 네트워크로 전송하고 있다. 이 경우 패킷 스니핑으로 패스워드가 노출될 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
try {
    Socket s = new Socket("taranis", 4444);
    PrintWriter o = new PrintWriter(s.getOutputStream(), true);
// 패스워드를 평문으로 전송하여 안전하지 않다.
    String password = getPassword();
    o.write(password);
} catch (FileNotFoundException e) {
    ……
```

아래 예제는 패스워드를 네트워크로 서버로 전송하기 전에 AES 등의 안전한 암호알고리즘으로 암호화한 안전한 프로그램이다.

**안전한 코드의 예 JAVA**

```java
// 패스워드를 암호화 하여 전송
try {
    Socket s = new Socket("taranis", 4444);
    PrintStream o = new PrintStream(s.getOutputStream(), true);
// 패스워드를 강력한 AES암호화 알고리즘으로 전송하여 사용한다.
    Cipher c = Cipher.getInstance("AES/CBC/PKCS5Padding");

    String password = getPassword();
    byte[] encPassword = c.update(password.getBytes());
  o.write(encPassword, 0, encPassword.length);
} catch (FileNotFoundException e) {
        ……
```

아래 C# 예제 또한 패스워드를 암호화하지 않고 네트워크로 전송하고 있다. 이 경우 패킷 스니핑으로 패스워드가 노출될 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
public void EmailPassword_OnClick(object sender, EventArgs args)
{
    MembershipUser u = Membership.GetUser(UsernameTextBox.Text, false);
    String password;

    if (u != null)
    {
        try
        {
            password = u.GetPassword(); // sensitive data created
        }
        catch (Exception e)
        {
            Msg.Text = "An exception occurred retrieving your password: " +
        Server.HtmlEncode(e.Message);
         return;
        }
        MailMessage Message = new MailMessage();
        Message.Body = "Your password is: " + Server.HtmlEncode(password);
//패스워드가 포함된 메시지를 네트워크로 전송하고 있다.
        SmtpMail.Send(Message);
        Msg.Text = "Password sent via e-mail.";
    }
    else
    {
        Msg.Text = "User name is not valid. Please check the value and try again.";
    }
}
```

패스워드를 네트워크로 전송할 때에는 암호화 하는 것이 바람직하다.

**안전한 코드의 예 C#**

```csharp
public void EmailPassword_OnClick(object sender, EventArgs args)
{
    MembershipUser u = Membership.GetUser(UsernameTextBox.Text, false);
    String password;

    if (u != null)
    {
        try
        {
            password = u.GetPassword();
            byte[] data = System.Text.Encoding.ASCII.GetBytes(password);
            data = new
            System.Security.Cryptography.SHA256Managed().ComputeHash(data);
            String hashedPassword = System.Text.Encoding.ASCII.GetString(data);
        }
        catch (Exception e)
        {
            Msg.Text = "An exception occurred retrieving your password: " +
        Server.HtmlEncode(e.Message);
            return;
        }
        MailMessage Message = new MailMessage();
        Message.Body = "Your password is: " + Server.HtmlEncode(hasedPassword);
        SmtpMail.Send(Message);
        Msg.Text = "Password sent via e-mail.";
    }
    else
    {
        Msg.Text = "User name is not valid. Please check the value and try again.";
    }
}
```

파일에서 읽어온 패스워드를 바로 사용하는 C예제 코드이다.

**안전하지 않은 코드의 예 C**

```c
int dbaccess() {
  FILE *fp; char *server = "DBserver";
  char passwd[20];
  char user[20];
  SQLHENV henv;
  SQLHDBC hdbc;
  fp = fopen("config", "r");
  fgets(user, sizeof(user), fp);
// 패스워드를 파일에서 읽어온다.
  fgets(passwd, sizeof(passwd), fp);
  fclose(fp);
  SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &henv);
  SQLAllocHandle(SQL_HANDLE_DBC, henv, &hdbc);
  SQLConnect(hdbc,
                         (SQLCHAR*) server,
                         (SQLSMALLINT) strlen(server),
                         (SQLCHAR*) user,
                         (SQLSMALLINT) strlen(user),
                         // 패스워드 암호화 없이 직접 연결한다.
                         (SQLCHAR*) passwd,
                         (SQLSMALLINT) strlen(passwd) );
  return 0;
```

외부에서 입력된 패스워드는 검증 과정을 거쳐 사용해야 한다.

**안전한 코드의 예 C**

```c
int dbaccess() {
    FILE *fp; char *server = "DBserver";
    char passwd[20];
    char user[20];
    char *encPasswd;
    char *key;
    SQLHENV henv;
    SQLHDBC hdbc;
    // AES-CBC로 암호화 모드를 설정한다.
    HCkCrypt2 crypt = CkCrypt2_putCryptAlgorithm(crypt,”aes”);
    CkCrypt2_putCipherMode(crypt,”cbc”);
    // 외부에서 암호화 키를 불러와 설정한다.
    key = getenv(“encrypt_key”);
    CkCrypt2_SetEncodedKey(crypt,key,”hex”);
    fp = fopen("config", "r");
    fgets(user, sizeof(user), fp);
    // 패스워드를 파일에서 읽어온다.
    fgets(passwd, sizeof(passwd), fp);
    fclose(fp);
    // 패스워드 암호화를 진행한다.
    encPasswd = CkCrypt2_encryptStringENC(crypt, passwd);
    SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &henv);
    SQLAllocHandle(SQL_HANDLE_DBC, henv, &hdbc);
    SQLConnect(hdbc,
                          (SQLCHAR*) server,
                          (SQLSMALLINT) strlen(server),
                          (SQLCHAR*) user,
                           (SQLSMALLINT) strlen(user),
                        // 암호화된 패스워드를 사용한다.
                          (SQLCHAR*) encPasswd,
                           (SQLSMALLINT) strlen(verifiedPwd) );
    return 0;
}
```

#### 라. 참고자료

- ① CWE-312, Cleartext Storage of Sensitive Information, MITRE, http://cwe.mitre.org/data/definitions/312.html
- ② Clear sensitive information stored in reusable resources, CERT, http://www.securecoding.cert.org/confluence/display/c/MEM03-C.+Clear+sensitive+information+stored+in+reusable+resources
- ③ Be careful while handling sensitive data, such as passwords, in program code, CERT, http: //www.securecoding.cert.org/confluence/display/c/MSC18-C.+Be+careful+while+handling+sensitive+data%2C+such+as+passwords%2C+in+program+code
- ④ Never hard code sensitive information, CERT, http://www.securecoding.cert.org/confluence/display/java/MSC03-J.+Never+hard+code+sensitive+information
- ⑤ Do not store unencrypted sensitive information on the client side, CERT, http://www.securecoding.cert.org/confluence/display/java/FIO52-J.+Do+not+store+unencrypted+sensitive+information+on+the+client+side
- ⑥ Password Plaintext Storage, OWASP https://www.owasp.org/index.php/Password_Plaintext_Storage
- ⑦ CWE-319, Cleartext Transmission of Sensitive Information, MITRE, http://cwe.mitre.org/data/definitions/319.html
- ⑧ Insecure Transport, OWASP, https://www.owasp.org/index.php/Insecure_Transport
### 6. 하드코드된 중요정보

#### 가. 개요

프로그램 코드 내부에 하드코드된 패스워드 또는 암호화키를 포함하여 내부 인증에 사용하거나 암호화를 수행하면 중요정보(관리자 정보, 암호화된 정보 등)가 유출될 수 있는 보안약점이다.

#### 나. 보안대책

패스워드는 암호화 하여 별도의 파일에 저장하여 사용한다. 또한 중요정보를 암호화하면, 상수가 아닌 암호화 키를 사용하도록 하며 소스코드 내부에 상수형태의 암호화 키를 저장해서 사용하지 않도록 한다.

#### 다. 코드예제

- 하드코드된 비밀번호
데이터베이스 연결을 위한 패스워드를 소스코드 내부에 상수 형태로 하드코딩 하는 경우, 접속 정보가 노출될 수 있어 위험하다.

**안전하지 않은 코드의 예 JAVA**

```java
public class MemberDAO {
   private static final String DRIVER = "oracle.jdbc.driver.OracleDriver";
   private static final String URL = "jdbc:oracle:thin:@192.168.0.3:1521:ORCL";
   private static final String USER = "SCOTT"; // DB ID;
// DB 패스워드가 소스코드에 평문으로 저장되어 있다.
  private static final String PASS = "SCOTT"; // DB PW;
……
   public Connection getConn() {
       Connection con = null;
       try {
            Class.forName(DRIVER);
            con = DriverManager.getConnection(URL, USER, PASS);
 ……
```

패스워드는 안전한 암호화 방식으로 암호화하여 별도의 분리된 공간(파일)에 저장해야 하며, 암호화된 패스워드를 사용하기 위해서는 복호화 과정을 거쳐야 한다.

**안전한 코드의 예 JAVA**

```java
public class MemberDAO {
    private static final String DRIVER = "oracle.jdbc.driver.OracleDriver";
    private static final String URL = "jdbc:oracle:thin:@192.168.0.3:1521:ORCL";
    private static final String USER = "SCOTT"; // DB ID
  ……
    public Connection getConn() {
       Connection con = null;
       try {
        Class.forName(DRIVER);
// 암호화된 패스워드를 프로퍼티에서 읽어들여 복호화해서 사용해야한다.
           String PASS = props.getProperty("EncryptedPswd");
           byte[] decryptedPswd = cipher.doFinal(PASS.getBytes());
           PASS = new String(decryptedPswd);
           con = DriverManager.getConnection(URL, USER, PASS);
 ……
```

Credential 객체를 생성하기 위한 패스워드를 소스코드 내부에 상수 형태로 하드코딩 하는 경우, 접속 정보가 노출될 수 있어 위험하다.

**안전하지 않은 코드의 예 C#**

```csharp
string UserName = "username";
string Password = "password";
// 평문으로 저장된 패스워드를 이용하여 NetworkCredential 생성
NetworkCredential myCred = new NetworkCredential(UserName, Password);
```

암호화된 패스워드로 Credential 객체를 생성한다.

**안전한 코드의 예 C#**

```csharp
string UserName = "username";
string Password = "password";
SecureString SecurelyStoredPassword = new SecureString();

foreach (char c in Password)
{
    SecurelyStoredPassword.AppendChar(c);
}

// 암호화된 패스워드를 사용하여 NetworkCredential 생성
NetworkCredential secure_myCred = new NetworkCredential(UserName,
   SecurelyStoredPassword);
```

하드코드된 패스워드를 바로 사용하는 C예제 코드이다.

**안전하지 않은 코드의 예 C**

```c
int dbaccess(char *server, char *user) {
    SQLHENV henv;
    SQLHDBC hdbc;
    char *password = “password”;
    SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &henv);
  SQLAllocHandle(SQL_HANDLE_DBC, henv, &hdbc);
// 하드코드된 패스워드를 사용
    SQLConnect(hdbc,(SQLCHAR*)server,strlen(server),user,strlen(user),
      password, strlen(password));
    return 0;
```

패스워드는 코드 상에서 보이지 않게 사용해야 한다. 아래의 예제는 환경 변수를 이용하여 패스워드를 사용한다.

**안전한 코드의 예 C**

```c
int dbaccess(char *server, char *user, char *passwd) {
    SQLHENV henv;
    SQLHDBC hdbc;
    // 패스워드를 외부에서 불러와서 사용
    char *password = getenv(“password”);
    SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &henv);
    SQLAllocHandle(SQL_HANDLE_DBC, henv, &hdbc);
    SQLConnect(hdbc, (SQLCHAR*) server, strlen(server), user, strlen(user),
     password, strlen(password));
    SQLFreeHandle(SQL_HANDLE_DBC, hdbc);
    SQLFreeHandle(SQL_HANDLE_ENV, henv);
    return 0;
}
```

- 하드코드된 암호화 키
소스코드 내부에 암호화 키를 상수 형태로 하드코딩하여 사용하면 악의적인 공격자에게 암호화 키가 노출될 위협이 있다.

**안전하지 않은 코드의 예 JAVA**

```java
import javax.crypto.KeyGenerator;
import javax.crypto.spec.SecretKeySpec;
import javax.crypto.Cipher;
   ……
public String encriptString(String usr) {
// 암호화 키를 소스코드 내부에 사용하는 것은 안전하지 않다.
  String key = "22df3023sf~2;asn!@#/>as";
    if (key != null) {
         byte[] bToEncrypt = usr.getBytes("UTF-8");
         SecretKeySpec sKeySpec = new SecretKeySpec(key.getBytes(), "AES");
```

암호화 과정에 사용하는 암호화 키는 외부 공간(파일)에 안전한 방식으로 암호화하여 보관해야 하며, 암호화된 암호화 키는 복호화하여 사용한다.

**안전한 코드의 예 JAVA**

```java
import javax.crypto.KeyGenerator;
import javax.crypto.spec.SecretKeySpec;
import javax.crypto.Cipher;
   ……
public String encriptString(String usr) {
// 암호화 키는 외부 파일에서 암호화 된 형태로 저장하고, 사용시 복호화 한다.
  String key = getPassword("./password.ini");
  key = decrypt(key);
  if (key != null) {
       byte[] bToEncrypt = usr.getBytes("UTF-8");
     SecretKeySpec sKeySpec = new SecretKeySpec(key.getBytes(), "AES");
```

소스코드 내부에 암호화 키를 상수 형태로 하드코딩하여 사용하면 악의적인 공격자에게 암호화 키가 노출될 위협이 있다.

**안전하지 않은 코드의 예 C#**

```csharp
// 암호화 키를 소스코드 내부에 사용하는 것은 안전하지 않다.
byte[] key = new byte[] { 0x43, 0x87, 0x23, 0x72 };
byte[] iv = new byte[] { 0x43, 0x87, 0x23, 0x72 };
FileStream fStream = File.Open(fileName, FileMode.OpenOrCreate);

CryptoStream cStream = new CryptoStream(fStream,
  new TripleDESCryptoServiceProvider().CreateEncryptor(key, iv),
  CryptoStreamMode.Write);
```

암호화 과정에 사용하는 암호화 키는 외부 공간(파일)에 안전한 방식으로 암호화하여 보관해야 하며, 암호화된 암호화 키는 복호화하여 사용한다.

**안전한 코드의 예 C#**

```csharp
// 암호화 키는 외부 파일에서 암호화 된 형태로 저장하고, 사용시 복호화 한다.

byte[] key = GetKey(./password.ini);
byte[] iv = GetIV(./password.ini);
FileStream fStream = File.Open(fileName, FileMode.OpenOrCreate);

CryptoStream cStream = new CryptoStream(fStream,
     new TripleDESCryptoServiceProvider().CreateEncryptor(Decrypt(key),
     Decrypt(iv)),
     CryptoStreamMode.Write);
```

하드코드된 비밀번호를 사용할 경우, 코드에 접근 권한이 있는 사용자가 비밀번호를 알 수 있다.

**안전하지 않은 코드의 예 C**

```c
typedef int SQLSMALLINT;
int dbaccess(char *user, char *passwd) {
 char *server = "DBserver";
 char *cpasswd;
 SQLHENV henv;
 SQLHDBC hdbc;
 SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &henv);
 SQLAllocHandle(SQL_HANDLE_DBC, henv, &hdbc);
 // 암호화된 비밀번호와 솔트를 사용한다. 코드에 접근 권한이 있는 사용자는 해당 비밀번호와
    솔트를 획득할 수 있다.
     cpasswd = crypt(passwd, “salt”);
 if (strcmp(cpasswd, "68af404b513073582b6c63e6b") != 0) {
   // USE_OF_HARDCODED_CRYPTOGRAPHIC_KEY
     printf("Incorrect password \n");
     return -1;
 }
```

암호화되어 저장된 암호를 외부에서 불러오고 이를 비교하는 코드가 작성되어야 한다.

**안전한 코드의 예 C**

```c
extern char *salt;
typedef int SQLSMALLINT;
int dbaccess(char *user, char *passwd) {
    char *server = "DBserver";
    char *cpasswd;
    // 외부에 있는 암호화된 비밀번호와 솔트를 불러온다.
    char* storedpasswd = getenv(“password”);
    char* salt = getenv(“salt”);
    SQLHENV henv;
    SQLHDBC hdbc;
    SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &henv);
    SQLAllocHandle(SQL_HANDLE_DBC, henv, &hdbc);
    // 외부에서 불러온 솔트 값을 사용해 비빌번호를 암호화한다.
    cpasswd = crypt(passwd, salt);
    // 암호화된 비밀번호와 외부에서 불러온 값을 비교한다.
    if (strcmp(cpasswd, storedpasswd) != 0) {
        printf("Incorrect password \n");
        SQLFreeHandle(SQL_HANDLE_DBC, &hdbc);
        SQLFreeHandle(SQL_HANDLE_ENV, &henv);
        return -1;
    }
}
```

#### 라. 참고자료

- ① CWE-259 Use of Hard-coded Password, MITRE, http://cwe.mitre.org/data/definitions/259.html
- ② Be careful while handling sensitive data, such as passwords, in program code, CERT, http: //www.securecoding.cert.org/confluence/display/c/MSC18-C.+Be+careful+while+handling+sensitive+data,+such+as+passwords,+in+program+code
- ③ Password Management: Hardcoded Password, OWASP, https://www.owasp.org/index.php/Password_Management:_Hardcoded_Password
- ④ CWE-321 Use of Hard-coded Cryptographic Key, MITRE, http://cwe.mitre.org/data/definitions/321.html
- ⑤ Be careful while handling sensitive data, such as passwords, in program code, CERT, http: //www.securecoding.cert.org/confluence/display/c/MSC18-C.+Be+careful+while+handling+sensitive+data,+such+as+passwords,+in+program+code
- ⑥ Use of hard-coded password, OWASP, https://www.owasp.org/index.php/Use_of_hard-coded_password
### 7. 충분하지 않은 키 길이 사용

#### 가. 개요

길이가 짧은 키를 사용하는 것은 암호화 알고리즘을 취약하게 만들 수 있다. 키는 암호화 및 복호화에 사용되는데, 검증된 암호화 알고리즘을 사용하더라도 키 길이가 충분히 길지 않으면 짧은 시간 안에 키를 찾아낼 수 있고 이를 이용해 공격자가 암호화된 데이터나 패스워드를 복호화 할 수 있게 된다.

#### 나. 보안대책

RSA 알고리즘은 적어도 2,048 비트 이상의 길이를 가진 키와 함께 사용해야 하고, 대칭암호화 알고리즘(Symmetric Encryption Algorithm)의 경우에는 적어도 128비트 이상의 키를 사용한다.

#### 다. 코드예제

다음의 예제는 보안성이 강한 RSA 알고리즘을 사용함에도 불구하고, 키 사이즈를 작게 설정함으로써 프로그램의 보안약점을 야기한 경우이다.

**안전하지 않은 코드의 예 JAVA**

```java
public static final String ALGORITHM = "RSA";
public static final String PRIVATE_KEY_FILE = "C:/keys/private.key";
public static final String PUBLIC_KEY_FILE = "C:/keys/public.key";
public static void generateKey() {
   try {
           final KeyPairGenerator keyGen = KeyPairGenerator.getInstance(ALGORITHM);
// RSA 키 길이를 1024 비트로 짧게 설정하는 경우 안전하지 않다.
           keyGen.initialize(1024);
           final KeyPair key = keyGen.generateKeyPair();
           File privateKeyFile = new File(PRIVATE_KEY_FILE);
                 File publicKeyFile = new File(PUBLIC_KEY_FILE);
```

공개키 암호화에 사용하는 키의 길이는 적어도 2048비트 이상으로 설정한다.

**안전한 코드의 예 JAVA**

```java
public static final String ALGORITHM = "RSA";
public static final String PRIVATE_KEY_FILE = "C:/keys/private.key";
public static final String PUBLIC_KEY_FILE = "C:/keys/public.key";
public static void generateKey() {
   try {
        final KeyPairGenerator keyGen = KeyPairGenerator.getInstance(ALGORITHM);
        keyGen.initialize(2048);
        final KeyPair key = keyGen.generateKeyPair();
        File privateKeyFile = new File(PRIVATE_KEY_FILE);
        File publicKeyFile = new File(PUBLIC_KEY_FILE);
```

다음의 예제는 보안성이 강한 RSA 알고리즘을 사용함에도 불구하고, 키 사이즈를 작게 설정함으로써 프로그램의 보안약점을 야기한 경우이다.

**안전하지 않은 코드의 예 C#**

```csharp
static string UseRSA(string input) {
 // RSA 키 길이를 1024 비트로 짧게 설정하는 경우 안전하지 않다.
    var rsa = new RSACryptoServiceProvider(1024);
    ...
  }
```

공개키 암호화에 사용하는 키의 길이는 적어도 2048비트 이상으로 설정한다.

**안전한 코드의 예 C#**

```csharp
static string UseRSA(string input) {
// RSA 키 길이를 2048 비트 이상으로 길게 설정한다.
    var rsa = new RSACryptoServiceProvider(2048);
    ...
   }
```

다음의 예제는 보안성이 강한 RSA 알고리즘을 사용함에도 불구하고, 키 사이즈를 작게 설정함으로써 프로그램의 보안약점을 야기한 경우이다.

**안전하지 않은 코드의 예 C**

```c
EVP_PKEY *RSAKey() {
  EVP_PKEY *pkey;
  RSA *rsa;
// RSA 키 길이를 512 비트로 짧게 설정하는 경우 안전하지 않다.
  rsa = RSA_generate_key(512, 35, NULL, NULL);
  if(rsa == NULL) {
    printf("Error \n");
    return NULL;
  }
 pkey = EVP_PKEY_new();
 EVP_PKEY_assign_RSA(pkey, rsa);
 return pkey;
```

공개키 암호화에 사용하는 키의 길이는 적어도 2048비트 이상으로 설정한다.

**안전한 코드의 예 C**

```c
EVP_PKEY *RSAKey() {
  EVP_PKEY *pkey;
  RSA *rsa;
// 2048비트 이상으로 설정한 후에 사용해야 한다.
  rsa = RSA_generate_key(2048, 35, NULL, NULL);
  if(rsa == NULL) {
    printf("Error \n");
    return NULL;
  }
  pkey = EVP_PKEY_new();
  EVP_PKEY_assign_RSA(pkey, rsa);
  return pkey;
}
```

#### 라. 참고자료

- ① CWE-326 Inadequate Encryption Strength, MITRE, http://cwe.mitre.org/data/definitions/326.html
### 8. 적절하지 않은 난수값 사용

#### 가. 개요

예측 가능한 난수를 사용하는 것은 시스템에 보안약점을 유발한다. 예측 불가능한 숫자가 필요한 상황에서 예측 가능한 난수를 사용한다면, 공격자는 SW에서 생성되는 다음 숫자를 예상하여 시스템을 공격하는 것이 가능하다.

#### 나. 보안대책

컴퓨터의 난수발생기는 난수 값을 결정하는 시드(Seed)값이 고정될 경우, 매번 동일한 난수값이 발생 한다. 이를 최대한 피하기 위해 Java에서는 Random()과 Math.random() 사용 시 java.util. Random 클래스에서 기본값으로 현재시간을 기반으로 조합하여 매번 변경 되는 시드(Seed)값을 사용하며, C 에서는 rand()함수 사용 시 매번 변경되는 기본 시드(Seed)값이 없으므로, srand()로 매번 변경 되는 현재시간 기반 등으로 시드(Seed)값을 설정 하여야 한다.

그러나 세션 ID, 암호화키 등 보안결정을 위한 값을 생성하고 보안결정을 수행하는 경우에는, Java 에서 Random()과 Math.random()을 사용하지 말아야 하며, 예측이 거의 불가능하게 암호학적으로 보호된 java.security.SecureRandom 클래스를 사용하는 것이 안전하다.

#### 다. 코드예제

java.util.Random 클래스의 random() 메소드 사용시, 고정된 seed를 설정하면 동일한 난수 값이 생성되어 안전하지 않다. 매번 변경되는 seed를 설정하더라도 보안결정을 위한 난수 이용시에는 안전하지 않다.

**안전하지 않은 코드의 예 JAVA**

```java
import java.util.Random;
...
public Static int getRandomValue(int maxValue) {
// 고정된 시드값을 사용하여 동일한 난수값이 생성되어 안전하지 않다.
    Random random = new Random(100);
    return random.nextInt(maxValue);

                              안전하지 않은 코드의 예 JAVA

}
public Static String getAuthKey() {
// 매번 변경되는 시드값을 사용하여 다른 난수값이 생성되나 보안결정을 위한 난수로는 안전하지 않다.
       Random random = new Random();
       String authKey = Integer.toString(random.nextInt());
```

java.util.Random 클래스는 setSeed로 매번 변경되는 시드값을 설정 하거나, 현재 시간 기반으로 매번 변경되는 별도 seed를 설정하지 않는 기본값을 사용한다. 보안결정을 위해 난수 사용 시에는 java.security.SecureRandom 클래스를 사용하는 것이 보다 안전하다.

**안전한 코드의 예 JAVA**

```java
import java.util.Random;
import java.security.SecureRandom;
...
public Static int getRandomValue(int maxValue) {
// setSeed로 매번 변경되는 시드값을 설정 하거나, 기본값인 현재 시간 기반으로 매번 변경되는
   시드값을 사용하도록 한다.
      Random random = new Random();
      return random.nextInt(maxValue);
}
public Static String getAuthKey() {
// 보안결정을 위한 난수로는 예측이 거의 불가능하게 암호학적으로 보호된 SecureRandom을
   사용한다.
try {
     SecureRandom secureRandom = SecureRandom.getInstance("SHA1PRNG");
    MessageDigest digest = MessageDigest.getInstance("SHA-256");
    secureRandom.setSeed(secureRandom.generateSeed(128));
    String authKey = new String(digest.digest((secureRandom.nextLong() +
    "").getBytes()));
...
} catch (NoSuchAlgorithmException e) {
```

보안결정을 위한 난수로는 안전하지 않은 C# 코드의 예제이다.

**안전하지 않은 코드의 예 C#**

```csharp
static int GenerateDigit()
{
    // 매번 변경되는 시드값을 사용하여 다른 난수값이 생성되나 보안결정을 위한 난수로는 안전하지 않다.
    Random rng = new Random();
    return rng.Next(10);
}
```

암호학적으로 보호된 SecureRandom 을 사용한다.

**안전한 코드의 예 C#**

```csharp
static int GenerateDigitGood()
{
// 보안결정을 위한 난수로는 예측이 거의 불가능하게 암호학적으로 보호된
   SecureRandom을 사용한다.
        byte[] b = new byte[4];
        new System.Security.Cryptography.RNGCryptoServiceProvider().GetBytes(b);
        return (b[0] & 0x7f) << 24 | b[1] << 16 | b[2] << 8 | b[3];
}
```

Seeding 없이 사용하는 rand() 함수는 암호화에 사용되기 힘듭니다.

**안전하지 않은 코드의 예 C**

```c
void foo() {
    int i;
    for(i=0; i<20; i++)
// 프로그램을 여러 번 실행 했을 때 얻는 결과 값이 같다. 범위가 작기 때문에 암호화에 사용되기
     힘들다.
     printf("%d", rand());
```

srandom(), random() 함수를 사용하면 보안적으로 안전한 난수를 얻을 수 있다.

**안전한 코드의 예 C**

```c
void foo() {
    srandom(time(NULL));
    int i;
    for(i=0; i<20; i++)
      printf("%ld", random());
}
```

#### 라. 참고자료

- ① CWE-330 Use of Insufficiently Random Values, MITRE, http://cwe.mitre.org/data/definitions/330.html
- ② Generate strong random numbers, CERT, http://www.securecoding.cert.org/confluence/display/java/MSC02-J.+Generate+strong+random+numbers
- ③ Do not use the rand() function for generating pseudorandom numbers, CERT, http://www.securecoding.cert.org/confluence/display/c/MSC30-C.+Do+not+use+the+rand%28%29+function+for+generating+pseudorandom+numbers
- ④ Insecure Randomness, OWASP, https://www.owasp.org/index.php/Insecure_Random ness
### 9. 취약한 비밀번호 허용

#### 가. 개요

사용자에게 강한 비밀번호 조합규칙을 요구하지 않으면, 사용자 계정이 취약하게 된다. 안전한 비밀번호를 생성하기 위해서는 「패스워드 선택 및 이용 안내서」의 안전한 패스워드 설정규칙을 적용해야 한다.

#### 나. 보안대책

비밀번호 생성 시 강한 조건 검증을 수행한다. 비밀번호(패스워드)는 숫자와 영문자, 특수문자 등을 혼합하여 정해진 자릿수를 사용하여 생성되도록 하고, 주기적으로 변경하도록 해야 한다.

#### 다. 코드예제

가입자가 입력한 비밀번호에 대한 복잡도 검증 없이 가입 승인 처리를 수행하고 있다.

**안전하지 않은 코드의 예 JAVA**

```java
String id = request.getParameter("id");
String pass = request.getParameter("pass");
UserVo userVO = new UserVo(id, pass);
……
// 비밀번호의 자릿수, 특수문자 포함 여부 등 복잡도를 체크하지 않고 등록
String result = registerDAO.register(userVO);
```

사용자 계정을 보호하기 위해 가입 시, 비밀번호 복잡도 검증 후 가입 승인처리를 수행한다.

**안전한 코드의 예 JAVA**

```java
String id = request.getParameter("id");
String pass = request.getParameter("pass");
// 비밀번호에 자릿수, 특수문자 포함 여부 등의 복잡도를 체크하고 등록하게 한다.
Pattern pattern = Pattern.compile("((?=.*[a-zA-Z])(?=.*[0-9@#$%]). {9, })");
Matcher matcher = pattern.matcher(pass);

                               안전한 코드의 예 JAVA

 if (!matcher.matches()) {
       return "비밀번호 조합규칙 오류";
 }
 UserVo userVO = new UserVo(id, pass);
 ……
 String result = registerDAO.register(userVO);
```

빈 비밀번호를 허용하는 C# 코드의 예제이다.

**안전하지 않은 코드의 예 C#**

```csharp
// 빈 비밀번호를 허용
NetworkCredential myCred = new NetworkCredential(UserName, "");
```

빈 비밀번호를 허용하지 않도록 한다.

**안전한 코드의 예 C#**

```csharp
// 빈 비밀번호를 사용하지 않음
NetworkCredential secure_myCred = new NetworkCredential(UserName, Password);
```

비밀번호에 대한 검증 없이 사용하는 C코드 예제이다.

**안전하지 않은 코드의 예 C**

```c
bool authentication(char* id, char* pwd)
{
  MYSQL *connectInstance;
  connectInstance = mysql_init(NULL);
// 패스워드 값에 대한 검증없이 사용한다.
   mysql_real_connect(connectInstance, "192.168.100.211", id, pwd,
    "database", 0, NULL, 0);
   ...
```

비밀번호에 대한 적절한 검증이 필요하다.

**안전한 코드의 예 C**

```c
bool authentication(char* id, char* pwd)
{
    MYSQL *connectInstance;
    connectInstance = mysql_init(NULL);
// 패스워드에 대한 적절한 검증을 수행해야 한다.
     if( checkValidationId( id ) == true && checkValidationPwd( pwd ) == true )
    {
        mysql_real_connect(connectInstance, "192.168.100.211", id, pwd,
          "database", 0, NULL, 0);
 }
 ...
}
```

#### 라. 참고자료

- ① CWE-521 Weak Password Requirements, MITRE, http://cwe.mitre.org/data/definitions/521.html
- ② Password Complexity, OWASP https://www.owasp.org/index.php/Authentication_Cheat_Sheet#Implement_Proper_Password_Strength_Controls
### 10. 부적절한 전자서명 확인

#### 가. 개요

전자서명이란 서명자의 신원을 확인하고 서명된 파일의 무결성을 보장할 수 있는 디지털 정보이다. 전자서명이 사용된 경우, 전자서명을 검증하지 않거나 검증절차가 부적절하면 위변조된 파일으로 악성코드에 감염될 수 있으므로 전자서명을 확인하여 위변조 여부를 판별하고 사용해야 한다.

#### 나. 보안대책

전자서명을 포함하는 파일을 사용할 때는 항상 전자서명을 확인하여야 한다. 이 경우, 전자서명 파일의 출처 등을 확인하여 신뢰할 수 없는 곳에서 생성된 파일을 사용하지 않도록 한다.

#### 다. 코드예제

다음 예제는 신뢰할 수 없는 곳에서 다운로드 한 JAR 파일의 서명을 확인하지 않고 사용한다. 이 경우, 악성코드가 삽입되어 실행될 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
 File f = new File(downloadedFilePath);
JarFile jf = new JarFile(f);
```

아래 예제는 JarFile 생성자에 boolean형 파라미터를 사용하여 전자서명을 확인한다. 전자서명 여부를 확인한 후, JarEntry.getCodeSigners() 메소드를 사용하여 JAR 객체에 대한 전자서명 주체를 신뢰할 수 있는지 확인하여야 한다.

**안전한 코드의 예 JAVA**

```java
File f = new File(downloadedFilePath);
JarFile jf = new JarFile(f, true);
Enumeration<JarEntry> ens = jf.entries();
while (ens.hasMoreElements()) {
          JarEntry en = ens.nextElement();
          if (!en.isDirectory()) {
                    if (en.toString().equals(path)) {
                    byte[] data = readAll(jar.getInputStream(en), en.getSize());
                    CodeSigner[] signers = en.getCodeSigners();
                    ...
                    }
          }
}
jf.close();
```

#### 라. 참고자료

- ① CWE-347 : Improper Verification of Cryptographic Signature, MITRE, http://cwe.mitre.org/data/definitions/347.html
### 11. 부적절한 인증서 유효성 검증

#### 가. 개요

인증서를 확인하지 않거나 인증서 확인 절차를 적절하게 수행하지 않아, 악의적인 호스트에 연결되거나 신뢰할 수 없는 호스트에서 생성된 데이터를 수신하게 되는 보안약점이다.

#### 나. 보안대책

인증서를 사용하기 전에 인증서의 유효성을 확인한다. 인증서의 Common Name과 실제 호스트가 일치하는지, 신뢰된 발급기관(CA, RootCA)의 서명 여부, 인증서의 유효기간, 인증서의 해지여부, 안전한 암호화 알고리즘 사용 여부 확인 등으로 유효한 인증서인지 검증하는 절차를 구현하여야 한다.

#### 다. 코드예제

아래 예제는 SSL_get_verify_result의 결과값이 X509_V_ERR_SELF_SIGNED_CERT_IN_ CHAIN인 경우에 자체 서명된 인증서이다. 이 경우, 해당 어플리케이션이 악의적인 행위를 할 수 있다.

**안전하지 않은 코드의 예 C**

```c
if ((cert = SSL_get_peer_certificate(ssl)) && host)
foo=SSL_get_verify_result(ssl);
if ((X509_V_OK==foo) || X509_V_ERR_SELF_SIGNED_CERT_IN_CHAIN==foo))
// 자체 서명된 인증서일 수 있다.
```

아래 예제는 인증서 검증결과 X509_V_OK로 반환되더라도 호스트가 Common Name과 일치하는지 확인하지 않으므로 인증서가 허가된 호스트용이라는 것을 확신할 수 없다.

**안전하지 않은 코드의 예 C**

```c
cert = SSL_get_peer_certificate(ssl);
if (cert && (SSL_get_verify_result(ssl)==X509_V_OK)) {
/* CN 을 확인하지 않았지만 신뢰하고 진행한다. 이럴 경우, 공격자가 Common Name을
www.attack.com으로 설정하여 중간자 공격에 사용할 경우 데이터가 중간에서 복호화 되고 있음을
탐지하지 못한다. */
}
```

아래 예제는 인증서 DN 일치여부와 유효기간 등을 검증한다.

**안전한 코드의 예 JAVA**

```java
private boolean verifySignature(X509Certificate toVerify, X509Certificate signingCert) {
         /* 검증하려는 호스트 인증서(toVerify)와 CA인증서(signing Cert)의 DN(Distinguished
             Name)이 일치하는지 여부를 확인한다.*/
         if (!toVerify.getIssuerDN().equals(signingCert.getSubjectDN())) return false;
         try {
                   // 호스트 인증서가 CA인증서로 서명 되었는지 확인한다.
                   toVerify.verify(signingCert.getPublicKey());
                   // 호스트 인증서가 유효기간이 만료되었는지 확인한다.
                   toVerify.checkValidity();
                   return true;
         } catch (GeneralSecurityException verifyFailed) {
                   return false;
         }
}
```

또한, 유효기간이 남아 있는 인증서의 해지여부를 확인하기 위해서는 CRL(Certificate revocation lists)으로 인증서 해지목록 또는 OCSP(Online Certificate Status Protocol)으로 실시간 인증서 상태확인이 필요하다. CRL 리스트는 해당 인증서를 참조하여 인증기관에서 다운받을 수

있으며, 다운받은 CRL으로 해지된 인증서를 확인할 수 있다.

#### 라. 참고자료

- ① CWE-295: Improper Certificate Validation, MITRE, http://cwe.mitre.org/data/definitions/295.html
### 12. 사용자 하드디스크에 저장되는 쿠키를 통한 정보노출

#### 가. 개요

대부분의 웹 응용프로그램에서 쿠키는 메모리에 상주하며, 브라우저의 실행이 종료되면 사라진다. 프로그래머가 원하는 경우, 브라우저 세션에 관계없이 지속적으로 저장되도록 설정할 수 있으며, 이것은 디스크에 기록되고, 다음 브라우저 세션이 시작되었을 때 메모리에 로드된다. 개인정보, 인증 정보 등이 이와 같은 영속적인 쿠키(Persistent Cookie)에 저장된다면, 공격자는 쿠키에 접근할 수 있는 보다 많은 기회를 가지게 되며, 이는 시스템을 취약하게 만든다.

#### 나. 보안대책

쿠키의 만료시간은 세션이 지속되는 시간을 고려하여 최소한으로 설정하고 영속적인 쿠키에는 사용자 권한 등급, 세션ID 등 중요정보가 포함되지 않도록 한다.

#### 다. 코드예제

쿠키의 만료시간을 1년으로 과도하게 길게 설정하고 있다. 쿠키의 유효기간이 긴 경우 사용자 하드 디스크에 쿠키가 저장되며 저장된 쿠키는 쉽게 도용될 수 있으므로 취약하다.

**안전하지 않은 코드의 예 JAVA**

```java
Cookie loginCookie = new Cookie("rememberme", "YES");
// 쿠키의 만료시간을 1년으로 과도하게 길게 설정하고 있어 안전하지 않다.
loginCookie.setMaxAge(60*60*24*365);
response.addCookie(loginCookie);
```

쿠키의 만료시간은 해당 기능에 맞춰 최소로 설정하고 영속적인 쿠키에는 중요 정보가 포함되지 않도록 한다.

**안전한 코드의 예 JAVA**

```java
Cookie loginCookie = new Cookie("rememberme", "YES");
// 쿠키의 만료시간은 해당 기능에 맞춰 최소로 사용한다.
loginCookie.setMaxAge(60*60*24);
response.addCookie(loginCookie);
```

다음은 쿠키의 만료시간을 1년으로 과도하게 길게 설정하고 있는 C# 코드의 예제이다. 쿠키의 유효 기간이 긴 경우 사용자 하드디스크에 쿠키가 저장되며 저장된 쿠키는 쉽게 도용될 수 있으므로 취약하다.

**안전하지 않은 코드의 예 C#**

```csharp
HttpCookie cookie = Request.Cookies.Get(“ExampleCookie”);
// 쿠키의 만료시간을 1년으로 과도하게 길게 설정하고 있어 안전하지 않다.
cookie.Expires = DateTime.Now.AddMinutes(60.0*24.0*365.0);
Response.Cookies.Add(cookie);
```

쿠키의 만료 시간을 10분으로 설정하고 있는 C# 코드의 예제이다.

**안전한 코드의 예 C#**

```csharp
HttpCookie cookie = Request.Cookies.Get(“ExampleCookie”);
// 쿠키의 만료시간은 해당 기능에 맞춰 최소로 사용한다.
cookie.Expires = DateTime.Now.AddMinutes(10d);
Response.Cookies.Add(cookie);
```

#### 라. 참고자료

- ① CWE-539 Information Exposure Through Persistent Cookies, MITRE, http://cwe.mitre.org/data/definitions/539.html
- ② Do not store unencrypted sensitive information on the client side, CERT, http://www.securecoding.cert.org/confluence/display/java/FIO52-J.+Do+not+store+unencrypted+sensitive+information+on+the+client+side
- ③ Expire and Max-Age Attributes, OWASP, https://www.owasp.org/index.php/Session_Management_Cheat_Sheet#Expire_and_Max-Age_Attributes
### 13. 주석문 안에 포함된 시스템 주요정보

#### 가. 개요

패스워드를 주석문에 넣어두면 시스템 보안이 훼손될 수 있다. 소프트웨어 개발자가 편의를 위해서 주석문에 패스워드를 적어둔 경우, 소프트웨어가 완성된 후에는 그것을 제거하는 것이 매우 어렵게 된다. 또한, 공격자가 소스코드에 접근할 수 있다면, 아주 쉽게 시스템에 침입할 수 있다.

#### 나. 보안대책

주석에는 ID, 패스워드 등 보안과 관련된 내용을 기입하지 않는다.

#### 다. 코드예제

다음 예제는 개발자의 이해를 돕기 위한 목적 등 편리성을 위해 비밀번호를 주석문 안에 서술하고 제대로 지우지 않아서 보안약점이 발생한 경우이다.

**안전하지 않은 코드의 예 JAVA**

```java
// 주석문으로 DB연결 ID, 패스워드의 중요한 정보를 노출시켜 안전하지 않다.
// DB연결 root / a1q2w3r3f2!@
con = DriverManager.getConnection(URL, USER, PASS);
```

프로그램 개발 시에 주석문 등에 남겨놓은 사용자 계정이나 패스워드 등의 정보는 개발 완료 시에 확실하게 삭제하여야 한다.

**안전한 코드의 예 JAVA**

```java
// ID, 패스워드등의 중요 정보는 주석에 포함해서는 안된다.
con = DriverManager.getConnection(URL, USER, PASS);
```

주석에 패스워드를 포함하고 있는 C# 코드이다.

**안전하지 않은 코드의 예 C#**

```csharp
// 주석문으로 DB연결 ID, 패스워드의 중요한 정보를 노출시켜 안전하지 않다.
// DB연결 root / a1q2w3r3f2!@
conn = customGetConnection(USER, PASS);
```

프로그램 개발 시에 주석문 등에 남겨놓은 사용자 계정이나 패스워드 등의 정보는 개발 완료 시에 확실하게 삭제하여야 한다.

**안전한 코드의 예 C#**

```csharp
// ID, 패스워드등의 중요 정보는 주석에 포함해서는 안된다.
conn = customGetConnection(USER, PASS);
```

주석에 패스워드를 포함하고 있는 C 예제 코드이다.

**안전하지 않은 코드의 예 C**

```c
/* password is "admin" */
/* passwd is "admin" */
int verfiyAuth(char *ipasswd, char *orgpasswd) {
  char *admin = "admin";
 if(strncmp(ipasswd, oprgpasswd, sizeof(ipasswd)) != 0) {
     printf("Authentication Fail! \n");
 }
 return admin;
```

불필요한 주석은 삭제해야 한다.

**안전한 코드의 예 C**

```c
int verfiyAuth(char *ipasswd, char *orgpasswd) {
    char *admin = "admin";
    if(strncmp(ipasswd, oprgpasswd, sizeof(ipasswd)) != 0) {
        printf("Authentication Fail! \n");
    }
    return admin;
}
```

#### 라. 참고자료

- ① CWE-615 Information Exposure Through Comments, MITRE, http://cwe.mitre.org/data/definitions/615.html
### 14. 솔트 없이 일방향 해쉬함수 사용

#### 가. 개요

패스워드를 저장 시 일방향 해쉬함수의 성질을 이용하여 패스워드의 해쉬값을 저장한다. 만약 패스 워드를 솔트(Salt)없이 해쉬하여 저장한다면, 공격자는 레인보우 테이블과 같이 해쉬값을 미리 계산 하여 패스워드를 찾을 수 있게 된다.

#### 나. 보안대책

패스워드를 저장 시 패스워드와 솔트를 해쉬함수의 입력으로 하여 얻은 해쉬값을 저장한다.

#### 다. 코드예제

다음의 예제는 패스워드 저장 시 솔트 없이 패스워드에 대한 해쉬값을 얻는 과정을 보여준다.

**안전하지 않은 코드의 예 JAVA**

```java
public String getPasswordHash(String password) throws Exception {
   MessageDigest md = MessageDigest.getInstance("SHA-256");
// 해쉬에 솔트를 적용하지 않아 안전하지 않다.
    md.update(password.getBytes());
    byte byteData[] = md.digest();
    StringBuffer hexString = new StringBuffer();
    for (int i=0; i<byteData.length i++) {
        String hex=Integer.toHexString(0xff & byteData[i]);
        if (hex.length() == 1) {
           hexString.append('0');
          }
          hexString.append(hex);
    }
    return hexString.toString();
}
```

패스워드만을 해쉬함수의 입력으로 사용하기에 레인보우 테이블을 이용한 사전 공격이 가능하며, 이를 방지하기 위해 패스워드와 솔트를 함께 해쉬함수에 적용하여 사용한다.

**안전한 코드의 예 JAVA**

```java
public String getPasswordHash(String password, byte[] salt) throws Exception {
    MessageDigest md = MessageDigest.getInstance("SHA-256");
    md.update(password.getBytes());
// 해쉬 사용 시에는 원문을 찾을 수 없도록 솔트를 사용하여야 한다.
     md.update(salt);
     byte byteData[] = md.digest();
     StringBuffer hexString = new StringBuffer();
     for (int i=0; i<byteData.length i++) {
         String hex=Integer.toHexString(0xff & byteData[i]);
         if (hex.length() == 1) {
            hexString.append('0');
         }
         hexString.append(hex);
    }
    return hexString.toString()
}
```

다음의 예제는 패스워드 저장 시 솔트 없이 패스워드에 대한 해쉬값을 얻는 과정을 보여준다.

**안전하지 않은 코드의 예 C#**

```csharp
static void HashWithoutSalt()
{
    // 해쉬에 솔트를 적용하지 않아 안전하지 않다.
    var bytes = new byte[100];
    (new Random()).NextBytes(bytes);
    var source = bytes;
    var sha256 = new SHA256CryptoServiceProvider();
    sha256.ComputeHash(source);
}
```

패스워드만을 해쉬함수의 입력으로 사용하기에 레인보우 테이블을 이용한 사전 공격이 가능하며, 이를 방지하기 위해 패스워드와 솔트를 함께 해쉬함수에 적용하여 사용한다.

**안전한 코드의 예 C#**

```csharp
static void HashWithSalt(int saltLength)
{
      // 해쉬에 솔트를 적용하여 원문을 찾을 수 없게 한다.
      var bytes = new byte[100];
      (new Random()).NextBytes(bytes);
      var source = bytes;
      var sha256 = new SHA256CryptoServiceProvider();
      byte[] saltBytes = GenerateRandomCryptographicBytes(saltLength);
      List<byte> sourceWithSaltBytes = new List<byte>();
      sourceWithSaltBytes.AddRange(source);
      sourceWithSaltBytes.AddRange(sourceWithSaltBytes);
      sha256.ComputeHash(sourceWithSaltBytes.ToArray());
}
```

솔트 값 없이 해쉬를 생성하는 C코드의 예제이다.

**안전하지 않은 코드의 예 C**

```c
void GenerateHash(char* data)
{
    char[512] hashedData = {0 };
//솔트 값 부분이 NULL 로 되어있어 들어가지 않는다.
  MD5HashAlgorithm( data, hashedData, NULL );
...
```

솔트 값을 인자로 넘겨줘야 한다.

**안전한 코드의 예 C**

```c
void GenerateHash(char* data, char* salt)
{
    char hashedData[512] = {0 };
    MD5HashAlgorithm( data, hashedData, salt );
    ...
}
```

#### 라. 참고자료

- ① CWE-759, Use of a One-Way Hash without a Salt, MITRE, http://cwe.mitre.org/data/definitions/759.html
- ② Store passwords using a hash function, CERT, http://www.securecoding.cert.org/confluence/display/java/MSC62-J.+Store+ passwords+using+a+hash+function
- ③ Use_a_cryptographically_strong_credential-specific_salt, OWASP, https://www.owasp.org/index.php/Password_Storage_Cheat_Sheet#Use_a_cryptographically_strong_credential-specific_salt
### 15. 무결성 검사 없는 코드 다운로드

#### 가. 개요

원격으로부터 소스코드 또는 실행파일을 무결성 검사 없이 다운로드 받고, 이를 실행하는 제품들이 종종 존재한다. 이는 호스트 서버의 변조, DNS 스푸핑 (Spoofing) 또는 전송 시의 코드 변조 등의 방법을 이용하여 공격자가 악의적인 코드를 실행할 수 있도록 한다.

#### 나. 보안대책

DNS 스푸핑(Spoofing)을 방어할 수 있는 DNS lookup을 수행하고 코드 전송 시 신뢰할 수 있는 암호 기법을 이용하여 코드를 암호화한다. 또한 다운로드한 코드는 작업 수행을 위해 필요한 최소한의 권한으로 실행하도록 한다.

#### 다. 코드예제

이 예제는 URLClassLoader()으로 원격에서 파일을 다운로드한 뒤 로드하면서, 대상 파일에 대한 무결성 검사를 수행하지 않아 파일변조 등으로 인한 피해가 발생할 수 있는 경우이다. 이러한 경우 공격자는 악의적인 실행코드로 클래스의 내용을 수정할 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
URL[] classURLs = new URL[] { new URL("file:subdir/") };
URLClassLoader loader = new URLClassLoader(classURLs);
Class loadedClass = Class.forName("LoadMe", true, loader);
```

이를 안전한 코드로 변환하면 다음과 같다. 클래스를 로드하기 전 클래스의 체크섬(Checksum)을 실행하여 로드하는 코드가 변조되지 않았음을 확인한다.

**안전한 코드의 예 JAVA**

```java
// 공개키 방식의 암호화 알고리즘과 메커니즘을 이용하여 전송파일에 대한 시그니처를 생성하고
    파일의 변조유무를 판단한다. 서버에서는 Private Key를 가지고 MyClass를 암호화한다.
String jarFile = "./download/util.jar";
byte[] loadFile = FileManager.getBytes(jarFile);
loadFile = encrypt(loadFile, privateKey);
// jarFileName으로 암호화된 파일을 생성한다.
FileManager.createFile(loadFile, jarFileName);
// 클라이언트에서는 파일을 다운로드 받을 경우 Public Key로 복호화한다.
URL[] classURLs = new URL[] { new URL("http://filesave.com/download/util.jar") };
URLConnection conn = classURLs.openConnection();
InputStream is = conn.getInputStream();
// 입력 스트림을 jarFile명으로 파일을 출력한다.
 FileOutputStream fos = new FileOutputStream(new File(jarFile));
While (is.read(buf) != -1) {
    ......
}
byte[] loadFile = FileManager.getBytes(jarFile);
loadFile = decrypt(loadFile, publicKey);
// 복호화된 파일을 생성한다.
FileManager.createFile(loadFile, jarFile);
URLClassLoader loader = new URLClassLoader(classURLs);
Class loadedClass = Class.forName("MyClass", true, loader);
```

파일 무결성 검사를 하지 않고 파일을 다운로드하는 C#코드 예제이다.

**안전하지 않은 코드의 예 C#**

```csharp
public override bool DownloadFile()
     {
         var url = "https://www.somewhere.untrusted.com";
         var desDir = "D:/DestinationPath";
         string fileName = Path.GetFileName(url);
         string descFilePath = Path.Combine(desDir, fileName);
         try
         {
             WebRequest myre = WebRequest.Create(url);
         }
         catch (Exception ex)
         {
             throw new Exception(ex.Message);
         }
         try
         {
        byte[] fileData;
// 파일 무결성 검사 없이 다운로드
             using (WebClient client = new WebClient())
             {
                 fileData = client.DownloadData(url);
             }
             using (FileStream fs = new FileStream(descFilePath, FileMode.OpenOrCreate))
             {
                 fs.Write(fileData, 0, fileData.Length);
             }
             return true;
         }
         catch (Exception ex)
         {
 throw new Exception(ex.Message);
         }
     }
```

해쉬값등을 이용하여 파일 무결성 검사 후 다운로드를 해야 한다.

**안전한 코드의 예 C#**

```csharp
public override bool DownloadFile()
      {
           var url = "https://www.somewhere.untrusted.com";
           var desDir = "D:/DestinationPath";
           string fileName = Path.GetFileName(url);
           string descFilePath = Path.Combine(desDir, fileName);
           try
           {
                  WebRequest myre = WebRequest.Create(url);
              }
            catch (Exception ex)
           {
                  throw new Exception(ex.Message);
           }
           try
          {
                  byte[] fileData;
                  using (WebClient client = new WebClient())
                  {
                      fileData = client.DownloadData(url);
                  }
// 해쉬 값 등을 사용하여 다운로드 받은 파일 무결성 검사
            CheckIntegrity(fileData);
using (FileStream fs = new FileStream(descFilePath,
FileMode.OpenOrCreate))
                  {
                      fs.Write(fileData, 0, fileData.Length);
                  }
                  return true;
}
              catch (Exception ex)
           {
                  throw new Exception(ex.Message);
              }
       }
```

리턴 값을 이용하여 무결성 검사를 하지 않은 C코드의 예제이다.

**안전하지 않은 코드의 예 C**

```c
void foo() {
  /* ... */
  hFile = CreateFile((LPCWSTR)data,GENERIC_WRITE, 0, NULL,
    CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
  InternetQueryDataAvailable(m_hURL, &dwSize,0,0);
  InternetReadFile(m_hURL, lpBuffer, dwSize, &dwRead);
  WriteFile(hFile, lpBuffer, dwRead, &dwWritten, NULL);
  /* ... */
```

리턴 값을 이용하여 무결성을 확인한 후 사용해야 한다.

**안전한 코드의 예 C**

```c
void foo() {
   /* ... */
   hFile = CreateFile((LPCWSTR)data,GENERIC_WRITE, 0, NULL, CREATE_ALWAYS,
     FILE_ATTRIBUTE_NORMAL, NULL);
   InternetQueryDataAvailable(m_hURL, &dwSize,0,0);
   bool result = InternetReadFile(m_hURL, lpBuffer, dwSize, &dwRead);
   if, lp( result == true) {
WriteFile(hFileBuffer, dwRead, &dwWritten, NULL);
   }
  /* ... */
}
```

#### 라. 참고자료

- ① CWE-494 Download of Code Without Integrity Check, MITRE, http://cwe.mitre.org/data/definitions/494.html
- ② Do not rely on the default automatic signature verification provided by URLClassLoader and java.util.jar, CERT, http://www.securecoding.cert.org/confluence/display/java/SEC06-J.+Do+not+rely +on+the+default+automatic+signature+verification+provided+ by+URLClassLoader+and+java.util.jar
### 16. 반복된 인증시도 제한 기능 부재

#### 가. 개요

일정 시간 내에 여러 번의 인증을 시도하여도 계정잠금 또는 추가 인증 방법 등의 충분한 조치가 수행되지 않는 경우, 공격자는 성공할법한 ID와 비밀번호들을 사전(Dictionary)으로 만들고 무차별 대입 (brute-force)하여 로그인 성공 및 권한획득이 가능하다.

#### 나. 보안대책

인증시도 횟수를 적절한 횟수로 제한하고 설정된 인증실패 횟수를 초과했을 경우 계정을 잠금하거나 추가적인 인증과정을 거쳐서 시스템에 접근이 가능하도록 한다.

#### 다. 코드예제

다음 예제는 로그인 정보를 잘못 입력하였을 경우 다시 입력을 시도하는데 있어 제한이 없다. 따라서 공격자는 여러 가지 비밀번호로 인증을 재시도하여 올바른 비밀번호를 알아내고 로그인에 성공할 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
private static final String SERVER_IP = "127.0.0.1";
private static final int SERVER_PORT = 8080;
private static final int FAIL = -1;
public void login() {
  String username = null;
  String password = null;
  Socket socket = null;
  int result = FAIL;
  try {
        socket = new Socket(SERVER_IP, SERVER_PORT);
        //인증 실패에 대해 제한을 두지 않아 안전하지 않다.
        while (result == FAIL) {
        ...
        result = verifyUser(username, password);
}
```

다음 예제는 사용자 인증시도 횟수를 기록하는 MAX_ATTEMPTS 변수를 정의하고, 이를 인증시도 횟수를 제한하는 카운터로 사용함으로써 무차별 공격에 대응하는 코드이다.

**안전한 코드의 예 JAVA**

```java
private static final String SERVER_IP = "127.0.0.1";
private static final int SERVER_PORT = 8080;
private static final int FAIL = -1;
private static final int MAX_ATTEMPTS = 5;
public void login() {
    String username = null;
    String password = null;
    Socket socket = null;
    int result = FAIL;
    int count = 0;
    try {
         socket = new Socket(SERVER_IP, SERVER_PORT);
        // 인증 실패 및 시도 횟수에 제한을 두어 안전하다.
            while (result == FAIL && count < MAX_ATTEMPTS) {
            ...
            result = verifyUser(username, password);
            count++;
}

                                안전하지 않은 코드의 예 C

int validateUser(char *host, int port) {
    int socket = openSocketConnection(host, port);
    if (socket < 0) {
        printf("Unable to open socket connection");
        return(FAIL);
    }
    int isValidUser = 0;
    char nm[NAME_SIZE];
    char pw[PSWD_SIZE];
    // 인증시도 횟수를 제한하고 있지 않다.
    while (isValidUser==0) {

                                     안전하지 않은 코드의 예 C

         if (getNextMsg(socket, nm, NAME_SIZE) > 0) {
             if (getNextMsg(socket, pw, PSWD_SIZE) > 0) {
                     isValidUser = AuthenticateUser(nm, pw);
             }
         }
     }
     return(SUCCESS);
 }

                                        안전한 코드의 예 C

 #define MAX_ATTEMPTS 5

 int validateUser(char *host, int port) {
            ......
         // 연속적인 사용자 인증 시도에 대한 횟수를 제한
         int count = 0;
         while ((isValidUser==0) && (count<MAX_ATTEMPTS)) {
             if (getNextMsg(socket, nm, NAME_SIZE) > 0) {
                        if (getNextMsg(socket, pw, PSWD_SIZE) > 0) {
                             isValidUser = AuthenticateUser(nm, pw);
                        }
                 }
                 count++;
         }
         if (isValidUser) {
               return(SUCCESS);
         } else {
                     return(FAIL);
         }
 }
```

다음 예제는 로그인 정보를 잘못 입력하였을 경우 다시 입력을 시도하는 데 있어 제한이 없다. 따라서 공격자는 여러 가지 비밀번호로 인증을 재시도하여 올바른 비밀번호를 알아내고 로그인에 성공할 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
// 로그인 실패 시 아무런 제약이 없음
override protected void OnLoginError(EventArgs e)
{
    //do nothing
}
```

로그인 시도에 대한 횟수를 제한한다.

**안전한 코드의 예 C#**

```csharp
override protected void OnLoginError(EventArgs e)
       {
// 연속적인 사용자 인증 시도에 대한 횟수를 제한
            if(ViewState["LoginErrors"] == null)
               ViewState["LoginErrors"] = 0;
            int ErrorCount = (int)ViewState["LoginErrors"] + 1;
            ViewState["LoginErrors"] = ErrorCount;

            if((ErrorCount > 3) && Login1.PasswordRecoveryUrl !=
string.Empty)
            Response.Redirect(Login1.PasswordRecoveryUrl);
        }
```

#### 라. 참고자료

- ① CWE-307, Improper Restriction of Excessive Authentication Attempts, MITRE, http://cwe.mitre.org/data/definitions/307.html
- ② Blocking Brute Force Attacks, OWASP, https://www.owasp.org/index.php/Blocking_Brute_Force_Attacks
## 제3절 시간 및 상태

동시 또는 거의 동시 수행을 지원하는 병렬 시스템이나 하나 이상의 프로세스가 동작되는 환경에서 시간 및 상태를 부적절하게 관리하여 발생할 수 있는 보안약점이다.

### 1. 경쟁조건: 검사시점과 사용시점(TOCTOU)

#### 가. 개요

병렬시스템(멀티프로세스로 구현한 응용프로그램)에서는 자원(파일, 소켓 등)을 사용하기에 앞서 자원의 상태를 검사한다. 하지만, 자원을 사용하는 시점과 검사하는 시점이 다르기 때문에, 검사하는 시점(Time Of Check)에 존재하던 자원이 사용하던 시점(Time Of Use)에 사라지는 등 자원의 상태가 변하는 경우가 발생한다.

예를 들어, 프로세스 A와 B가 존재하는 병렬시스템 환경에서 프로세스 A는 자원사용(파일 읽기)에 앞서 해당 자원(파일)의 존재 여부를 검사(TOC) 한다. 이때는 프로세스 B가 해당 자원(파일)을 아직 사용(삭제)하지 않았기 때문에, 프로세스 A는 해당 자원(파일)이 존재한다고 판단한다. 그러나 프로세스 A가 자원 사용(파일읽기)을 시도하는 시점(TOU)에 해당 자원(파일)은 사용불가능 상태이기 때문에 오류 등이 발생할 수 있다.

이와 같이 하나의 자원에 대하여 동시에 검사시점과 사용시점이 달라 생기는 보안약점으로 인해 동기화 오류뿐만 아니라 교착상태 등과 같은 문제점이 발생할 수 있다.

#### 나. 보안대책

공유자원(예: 파일)을 여러 프로세스가 접근하여 사용할 경우, 동기화 구문을 사용하여 한 번에 하나의 프로세스만 접근 가능하도록(synchronized, mutex 등) 하는 한편, 성능에 미치는 영향을 최소화하기 위해 임계코드 주변만 동기화 구문을 사용한다.

#### 다. 코드예제

다음의 예제는 파일을 대한 읽기와 삭제가 두 개의 스레드에 동작하게 되므로 이미 삭제된 파일을 읽으려고 하는 레이스컨디션7이 발생할 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
  class FileMgmtThread extends Thread {
       private String manageType = "";
       public FileMgmtThread (String type) {
          manageType = type;
       }
    // 멀티쓰레드 환경에서 공유자원에 여러프로세스가 사용하여 동시에 접근할 가능성이 있어 안전
        하지 않다.
       public void run() {
         try {
           if (manageType.equals("READ")) {
             File f = new File("Test_367.txt");
             if (f.exists()) {
                BufferedReader br
                 = new BufferedReader(new FileReader(f));
                br.close();
              }
            } else if (manageType.equals("DELETE")) {
              File f = new File("Test_367.txt");
              if (f.exists()) {
                f.delete();
            } else { … }
          }
        } catch (IOException e) { … }
      }
    }
public class CWE367 {
  public static void main (String[] args) {
      FileMgmtThread fileAccessThread = new FileMgmtThread("READ");
```

> <sup>7</sup> 레이스컨디션(Race Condition): Race Condition은 두 개 이상의 프로세스가 공용 자원을 병행적으로(concurrently) 읽거나 쓸 때, 공용 데이터에 대한 접근이 어떤 순서에 따라 이루어졌는지에 따라 그 실행 결과가 달라지는 상황을 말한다

**안전하지 않은 코드의 예 JAVA**

```java
        FileMgmtThread fileDeleteThread = new FileMgmtThread("DELETE");
// 파일의 읽기와 삭제가 동시에 수행되어 안전하지 않다.
        fileAccessThread.start();
        fileDeleteThread.start();
    }
}
```

따라서 다음 예제와 같이 동기화 구문인 synchronized를 사용하여 공유자원 (Test_367.txt)에 대한 안전한 읽기/쓰기를 수행할 수 있도록 한다.

**안전한 코드의 예 JAVA**

```java
class FileMgmtThread extends Thread {
    private static final String SYNC = "SYNC";
    private String manageType = "";
    public FileMgmtThread (String type) {
        manageType = type;
    }
    public void run() {
// 멀티쓰레드 환경에서 synchronized를 사용하여 동시에 접근할 수 없도록 사용해야한다.
    synchronized(SYNC) {
          try {
            if (manageType.equals("READ")) {
                File f = new File("Test_367.txt");
                  if (f.exists()) {
                    BufferedReader br
                      = new BufferedReader(new FileReader(f));
                    br.close();
               }
             } else if (manageType.equals("DELETE")) {
                  File f = new File("Test_367.txt");
                  if (f.exists()) {
                    f.delete();
                  } else { … }
              }

                               안전한 코드의 예 JAVA

         } catch (IOException e) { … }
        }
    }
 }
 public class CWE367 {
   public static void main (String[] args) {
     FileMgmtThread fileAccessThread = new FileMgmtThread("READ");
     FileMgmtThread fileDeleteThread = new FileMgmtThread("DELETE");
     fileAccessThread.start();
     fileDeleteThread.start();
     }
  }
```

다음의 C# 코드도 파일에 동시에 접근하는 레이스 컨디션이 발생할 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
// 멀티쓰레드 환경에서 동시에 접근할 수 없도록 사용해야한다.
public void ReadFile(String f)
{
           if(File.Exists(f))
  {
    File.ReadAllLines(f);
    }
}
```

아래와 같은 코드를 추가하여 레이스 컨디션을 방지해야 한다.

**안전한 코드의 예 C#**

```csharp
// 멀티쓰레드 환경에서 동시에 접근할 수 없도록 사용해야한다.
[MethodImpl(MethodImplOptions.Synchronized)]
public void ReadFile(String f)
{

                                    안전한 코드의 예 C#

             if(File.Exists(f))
       {
           File.ReadAllLines(f);
           }.
       }
```

아래 C 코드는 공유 자원 account에 대해 lock을 설정하지 않아 경쟁 조건이 발생할 수 있다. 입금과 출금이 빈번하게 발생하는 상황에서 경쟁 조건이 발생하면 account의 값이 달라진다. 아래 ex1은 정상적으로 deposit과 withdraw가 호출되는 상황이고 ex2는 경쟁 조건이 발생하는 상황이다. 최종 account의 값이 0과 -100으로 다른 것을 확인할 수 있다.

(ex1)

deposit(100) 호출 : (account: 0) deposit(100) 종료 : (account: 100) withdraw(100) 호출: (account: 100) withdraw(100) 종료: (account: 0)

(ex2)

deposit(100) 호출 : (account: 0) withdraw(100) 호출: (account: 0) deposit(100) 종료 : (account: 100) withdraw(100) 종료: (account: -100)

**안전하지 않은 코드의 예 C**

```c
static volatile double account;
void deposit(int amount) {

// lock 없이 공유 자원에 접근
  account += amount;
}
void withdraw(int amount) {
  account -= amount;
}
```

아래 C 코드는 mutex_lock()으로 공유 자원에 대한 동시 접근을 제한한 것이다.

**안전한 코드의 예 C**

```c
static volatile double account;
static mtx_t account_lock;

void deposit(int amount) {
    // mutex_lock, mutex_unlock을 이용해 공유 자원 접근을 제한한다.
    mutex_lock(&account_lock);
    account += amount;
    mutex_unlock(&account_lock);
}

void withdraw(int amount) {
  mutex_lock(&account_lock);
    account -= amount;
    mutex_unlock(&account_lock);
}
```

#### 라. 참고자료

- ① CWE-367 Time-of-check Time-of-use(TOCTOU) Race Condition, MITRE, http://cwe.mitre.org/data/definitions/367.html
- ② Avoid TOCTOU race conditions while accessing files, CERT, http://www.securecoding.cert.org/confluence/display/c/FIO45-C.+Avoid+TOCTOU+race+conditions+while+accessing+files
### 2. 종료되지 않는 반복문 또는 재귀함수

#### 가. 개요

재귀의 순환횟수를 제어하지 못하여 할당된 메모리나 프로그램 스택 등의 자원을 과다하게 사용하면 위험하다. 대부분의 경우, 귀납 조건(Base Case)이 없는 재귀 함수는 무한 루프에 빠져들게 되고 자원고갈을 유발함으로써 시스템의 정상적인 서비스를 제공할 수 없게 한다.

#### 나. 보안대책

모든 재귀 호출 시, 재귀 호출 횟수를 제한하거나, 초기값을 설정(상수)하여 재귀 호출을 제한해야 한다.

#### 다. 코드예제

factorial 함수는 함수 내부에서 자신을 호출하는 재귀함수로, 재귀문을 빠져 나오는 조건을 정의하고 있지 않아 무한 재귀에 빠져 시스템 장애를 유발할 수 있다.

**안전하지 않은 코드의 예 C**

```c
#include <stdio.h>
int factorial(int i)
{
// 재귀함수 탈출 조건을 설정하지 않아 무한루프가 된다.
   return i * factorial(i - 1);
}
int main()
{
    int num = 5;
    int result = factorial(num);
    printf("%d! : %d\n", num, result);
    return 0;
}
```

재귀 함수를 구현할 때는 아래와 같이 재귀문을 빠져 나오는 조건인 귀납조건(Base case)을 반드시 구현해야 한다.

**안전한 코드의 예 C**

```c
#include <stdio.h>

int factorial(int I)
{
// 재귀함수 사용 시에는 아래와 같이 탈출 조건을 사용해야 한다.
    if (i <= 1) {
        return 1;
    }
    return i * factorial(i – 1);
}

int main()
{
    int num = 5;
    int result = factorial(num);
    printf("%d! : %d\n", num, result);
    return 0;
}
```

#### 라. 참고자료

- ① CWE-674 Uncontrolled Recursion, MITRE, http://cwe.mitre.org/data/definitions/674. html
- ② CWE-835, Loop with Unreachable Exit Condition ('Infinite Loop'),MITRE, http://cwe.mitre.org/data/definitions/835.html
## 제4절 에러처리

에러를 처리하지 않거나, 불충분하게 처리하여 에러 정보에 중요정보(시스템 내부정보 등)가 포함될 때, 발생할 수 있는 취약점으로 에러를 부적절하게 처리하여 발생하는 보안약점이다.

### 1. 오류 메시지 정보노출

#### 가. 개요

응용프로그램이 실행환경, 사용자 등 관련 데이터 또는 시스템의 내부데이터 등 민감한 정보를 포함하는 오류 메시지를 생성하여 외부에 제공하는 경우, 공격자의 악성 행위를 도울 수 있다. 예외 발생 시 예외 이름이나 스택 트레이스를 출력하는 경우, 프로그램 내부구조를 쉽게 파악할 수 있기 때문이다.

#### 나. 보안대책

오류 메시지는 정해진 사용자에게 유용한 최소한의 정보만 포함하도록 한다. 소스코드에서 예외 상황은 내부적으로 처리하고 사용자에게 시스템 내부 정보 등 민감한 정보를 포함하는 오류를 출력하지 않도록 미리 정의된 메시지를 제공하도록 설정한다.

#### 다. 코드예제

다음 예제는 오류 메시지에 예외 이름이나 오류추적 정보를 출력하여 프로그램 내부 정보가 유출되는 경우이다.

**안전하지 않은 코드의 예 JAVA**

```java
try {
        rd = new BufferedReader(new FileReader(new File(filename)));
} catch(IOException e) {
        // 에러 메시지로 스택 정보가 노출됨
        e.printStackTrace();
}

                               안전하지 않은 코드의 예 JAVA

catch(IOException e) {
        // 오류발생시 화면에 출력된 시스템 정보로 다른 공격의 빌미를 제공한다.
        System.err.print(e.getMessage());
}
```

아래 코드와 같이 예외 이름이나 오류추적 정보를 출력하지 않도록 한다.

**안전한 코드의 예 JAVA**

```java
try {
     rd = new BufferedReader(new FileReader(new File(filename)));
} catch(IOException e) {
        // 에러 코드와 정보를 별도로 정의하고 최소 정보만 로깅
        logger.error("ERROR-01: 파일 열기 에러");
}
```

다음 예제는 오류메시지에 예외 이름이나 오류추적 정보를 출력하여 프로그램 내부 정보가 유출되는 C#코드이다.

**안전하지 않은 코드의 예 C#**

```csharp
try
{
    //do something
}
catch (CustomException e)
{
    Console.WriteLine(e);
}
```

예외 관련한 최소한의 정보만 출력하도록 한다.

**안전한 코드의 예 C#**

```csharp
try
{
    //do something
}
catch (CustomException e)
{
    _log.Debug(“ERROR-01 : error information”);
}
```

#### 라. 참고자료

- ① CWE-209 Information Exposure Through an Error Message, MITRE, http://cwe.mitre.org/data/definitions/209.html
- ② CWE-497 Exposure of Sensitive System Information to an Unauthorized Control Sphere, MITRE, http://cwe.mitre.org/data/definitions/497.html
- ③ Do not allow exceptions to expose sensitive information, CERT, http://www.securecoding.cert.org/confluence/display/java/ERR01-J.+Do+not+allow+exceptions+to+expose+sensitive+information?focusedCommentId=61702253#comment-61702253
- ④ Error Handling, OWASP, https://www.owasp.org/index.php/Error_Handling
### 2. 오류 상황 대응 부재

#### 가. 개요

오류가 발생할 수 있는 부분을 확인하였으나, 이러한 오류에 대하여 예외 처리를 하지 않을 경우, 공격자는 오류 상황을 악용하여 개발자가 의도하지 않은 방향으로 프로그램이 동작하도록 할 수 있다.

#### 나. 보안대책

오류가 발생할 수 있는 부분에 대하여 제어문을 사용하여 적절하게 예외 처리(C/C++에서 if와 switch, Java에서 try-catch 등)를 한다.

#### 다. 코드예제

다음 예제는 try 블록에서 발생하는 오류를 포착(catch)하고 있지만, 그 오류에 대해서 아무 조치를 하고 있지 않음을 보여준다. 아무 조치가 없으므로 프로그램이 계속 실행되기 때문에 프로그램에서 어떤 일이 일어났는지 전혀 알 수 없게 된다.

**안전하지 않은 코드의 예 JAVA**

```java
protected Element createContent(WebSession s) {
             ……
    try {
        username = s.getParser().getRawParameter(USERNAME);
        password = s.getParser().getRawParameter(PASSWORD);
        if (!"webgoat".equals(username) || !password.equals("webgoat")) {
            s.setMessage("Invalid username and password entered.");
            return (makeLogin(s));
        }
    } catch (NullPointerException e) {
    // 요청 파라미터에 PASSWORD가 존재하지 않을 경우 Null Pointer Exception이 발생하고
       해당 오류에 대한 대응이 존재하지 않아 인증이 된 것으로 처리
    }
```

예외를 포착(catch)한 후, 각각의 예외 사항(Exception)에 대하여 적절하게 처리해야 한다.

**안전한 코드의 예 JAVA**

```java
protected Element createContent(WebSession s) {
                ……
    try {
            username = s.getParser().getRawParameter(USERNAME);
            password = s.getParser().getRawParameter(PASSWORD);
            if (!"webgoat".equals(username) || !password.equals("webgoat")) {
                s.setMessage("Invalid username and password entered.");
                return (makeLogin(s));
            }
    } catch (NullPointerException e) {
    // 예외 사항에 대해 적절한 조치를 수행하여야 한다.
        s.setMessage(e.getMessage());
            return (makeLogin(s));
    }
```

다음의 C# 코드도 예외상황에 대한 조치가 없다.

**안전하지 않은 코드의 예 C#**

```csharp
try {
    InvokeMtd();
    } catch (CustomException e) {
     // 예외 상황에 대한 대응 부재
}
```

각각의 예외 상황에 대해 적절한 조치를 수행해야 한다.

**안전한 코드의 예 C#**

```csharp
try {
        InvokeMtd();
    } catch (CustomException e) {
// 예외 상황에 대해 적절한 조치를 수행하여야 한다.
        logger.Debug(“log message”);
}
```

#### 라. 참고자료

- ① CWE-390 Detection of Error Condition Without Action, MITRE, http://cwe.mitre.org/data/definitions/390.html
- ② Do not suppress or ignore checked exceptions, CERT, http://www.securecoding.cert.org/confluence/display/java/ERR00-J.+Do+not+suppress+or+ignore+checked+exceptions
### 3. 부적절한 예외 처리

#### 가. 개요

프로그램 수행 중에 함수의 결과값에 대한 적절한 처리 또는 예외 상황에 대한 조건을 적절하게 검사하지 않을 경우, 예기치 않은 문제를 야기할 수 있다.

#### 나. 보안대책

값을 반환하는 모든 함수의 결과값을 검사하여, 그 값이 의도했던 값인지 검사하고, 예외 처리를 사용하는 경우에 광범위한 예외 처리 대신 구체적인 예외 처리를 수행한다.

#### 다. 코드예제

다음 예제는 try 블록에서 다양한 예외가 발생할 수 있음에도 불구하고 예외를 세분화하지 않고 광범위한 예외 클래스인 Exception을 사용하여 예외를 처리하고 있다.

**안전하지 않은 코드의 예 JAVA**

```java
try {
        ...
    reader = new BufferedReader(new InputStreamReader(url.openStream()));
    String line = reader.readLine();
    SimpleDateFormat format = new SimpleDateFormat("MM/DD/YY");
   Date date = format.parse(line);
// 예외처리를 세분화 할 수 있음에도 광범위하게 사용하여 예기치 않은 문제가 발생 할 수 있다.
} catch (Exception e) {
    System.err.println("Exception : " + e.getMessage());
}
```

발생 가능한 예외를 세분화하고 발생 가능한 순서에 따라 예외를 처리하고 있다.

**안전한 코드의 예 JAVA**

```java
try {
         ...
         reader = new BufferedReader(new InputStreamReader(url.openStream()));
         String line = reader.readLine();
        SimpleDateFormat format = new SimpleDateFormat("MM/DD/YY");
        Date date = format.parse(line);
        // 발생할 수 있는 오류의 종류와 순서에 맞춰서 예외처리 한다.
} catch (MalformedURLException e) {
      System.err.println("MalformedURLException : " + e.getMessage());
} catch (IOException e) {
      System.err.println("IOException : " + e.getMessage());
} catch (ParseException e) {
         System.err.println("ParseException : " + e.getMessage());
}
```

다음 예제는 try 블록에서 다양한 예외가 발생할 수 있음에도 불구하고 예외를 세분화하지 않고 광범위한 예외 클래스인 Exception을 사용하여 예외를 처리하고 있다.

**안전하지 않은 코드의 예 C#**

```csharp
try {
    InvokeMtd();
// 예외처리를 세분화할 수 있음에도 광범위하게 사용하여 예기치 않은 문제가 발생할 수 있다.
        } catch (Exception e) {

}
```

발생 가능한 예외를 세분화하고 발생 가능한 순서에 따라 예외를 처리하고 있다.

**안전한 코드의 예 C#**

```csharp
ry {
       InvokeMtd();
// 발생할 수 있는 오류의 종류와 순서에 맞춰서 예외처리 한다.
    } catch (IOException e) {
    logger.Debug(“IOException log here”);
} catch (SQLException e){
    logger.Debug(“SQLException log here”);
}
```

#### 라. 참고자료

- ① CWE-754 Improper Check for Unusual or Exceptional Conditions, MITRE, http://cwe.mitre.org/data/definitions/754.html
- ② Do not complete abruptly from a finally block, CERT, http://www.securecoding.cert.org/confluence/display/java/ERR04-J.+Do+not+complete+abruptly+from+a+finally+block
- ③ Exception Handling in Spring MVC, Spring, http://spring.io/blog/2013/11/01/exception -handling-in-spring-mvc
## 제5절 코드오류

타입 변환 오류, 자원(메모리 등)의 부적절한 반환 등과 같이 개발자가 범할 수 있는 코딩오류로 인해 유발되는 보안약점이다.

### 1. Null Pointer 역참조

#### 가. 개요

널 포인터(Null Pointer) 역참조는 ‘일반적으로 그 객체가 널(Null)이 될 수 없다’라고 하는 가정을 위반했을 때 발생한다. 공격자가 의도적으로 널 포인터 역참조를 발생시키는 경우, 그 결과 발생하는 예외 상황을 이용하여 추후의 공격을 계획하는 데 사용될 수 있다.

#### 나. 보안대책

널이 될 수 있는 레퍼런스(Reference)는 참조하기 전에 널 값인지를 검사하여 안전한 경우에만 사용한다.

#### 다. 코드예제

다음의 예제의 경우 obj가 null이고, elt가 null이 아닌 경우 널(Null) 포인터 역참조가 발생한다.

**안전하지 않은 코드의 예 JAVA**

```java
public static int cardinality (Object obj, final Collection col) {
   int count = 0;
   if (col == null) {
      return count;
   }
   Iterator it = col.iterator();
   while (it.hasNext()) {

                                      안전하지 않은 코드의 예 JAVA

            Object elt = it.next();
// obj가 null이고 elt가 null이 아닐 경우, Null.equals 가 되어 널(Null) 포인터 역참조가 발생한다.
            if ((null == obj && null == elt) || obj.equals(elt)) {
                    count++;
            }
    }
    return count;
}
```

obj가 null인지 검사 후 참조해야 한다.

**안전한 코드의 예 JAVA**

```java
public static int cardinality (Object obj, final Collection col) {
        int count = 0;
        if (col == null) {
             return count;
        }
        Iterator it = col.iterator();
        while (it.hasNext()) {
                Object elt = it.next();
// obj를 참조하는 equals가 null이
       if ((null == obj && null == elt) || (null != obj && obj.equals(elt))) {
                      count++;
                }
        }
        return count;
}
```

다음 예제의 경우 request.getParameter에 의해 null이 들어오게 되면 널(Null) 포인터 역참조가 발생한다.

**안전하지 않은 코드의 예 JAVA**

```java
String url = reuqest.getParamter("url");
// url 에 null이 들어오면 널(Null) 포인터 역참조가 발생한다.
if ( url.equals("") )
```

null을 가질 수 있는 참조 변수를 사용해 객체의 속성이나 메소드를 사용하는 경우 null 검사를 수행하고 사용한다.

안전한코드의 예 JAVA

String url = reuqest.getParamter("url"); // null값을 가지는 참조 변수를 사용할 경우, null 검사를 수행하고 사용한다. if ( url != null || url.equals("") )

다음 예제의 경우 Request 객체에서 QeuryString을 사용하여 url의 파라미터 중 name 에 해당하는 값을 가져오는 코드이다. url의 파라미터에 name이 없으면 QueryString[“name”]은 null을 리턴 하게 되고, username은 null 값을 가지게 되어 널(Null) 포인터 역참조가 발생한다.

**안전하지 않은 코드의 예 C#**

```csharp
protected void Page_Load(object sender, EventArgs e) {
    // url 파라미터에 name 이 없으면 username은 null 값을 가지게 된다.
    string username = Request.QueryString[“name”];
    // null 값을 가지는 username을 참조하여 널(Null) 포인터 역참조가 발생한다.
    if (username.Length > 20) {
       // length error
    }
}
```

null을 가질 수 있는 참조 변수를 사용해 객체의 속성이나 메소드를 사용하는 경우 null 검사를 수행하고 사용한다.

**안전한 코드의 예 C#**

```csharp
protected void Page_Load(object sender, EventArgs e) {
    // url 파라미터에 name 이 없으면 username은 null 값을 가지게 된다.
     string username = Request.QueryString[“name”];
    // null 값을 가지는 username을 참조하기 전에 null 검사를 수행하므로 안전하다.
     if ( username != null && username > 20) {
         // length error
     }
}
```

아래 C 코드는 null 값을 반환할 수 있는 함수 IntegerAddressReturn()을 호출한다. P가 null 인 상태에서 p 값을 참조하면 널 포인터 역참조가 발생한다.

**안전하지 않은 코드의 예 C**

```c
void NullPointerDereference(int count) {
    // IntegerAddressReturn()이 0을 return 하면 p는 null 값을 가지게 된다.
    int *p = IntegerAddressReturn();
    // null 값을 가지는 p 값을 참조하여 널(Null) 포인터 역참조가 발생한다.
 *p = count;
}
```

아래 C 코드는 null 값을 가질 수 있는 p를 참조하기 전에 null 검사를 진행하므로 안전하다.

**안전한 코드의 예 C**

```c
void NullPointerDereference(int count) {
// IntegerAddressReturn()이 0을 return 하면 p는 null 값을 가지게 된다.
int *p = IntegerAddressReturn();
// 참조하기전에 null 검사를 수행하므로 안전하다.
If(p != 0) *p = count;
```

#### 라. 참고자료

- ① CWE-476 NULL Pointer Dereference, MITRE, http://cwe.mitre.org/data/definitions/476.html
- ② Do not dereference null pointers, CERT, http://www.securecoding.cert.org/confluence/display/c/EXP34-C.+Do+not+dereference+null+pointers
- ③ Null Dereference, OWASP, https://www.owasp.org/index.php/Null_Dereference
### 2. 부적절한 자원 해제

#### 가. 개요

프로그램의 자원, 예를 들면 열린 파일디스크립터(Open File Descriptor), 힙 메모리(Heap Memory), 소켓(Socket) 등은 유한한 자원이다. 이러한 자원을 할당받아 사용한 후, 더 이상 사용하지 않는 경우에는 적절히 반환하여야 하는데, 프로그램 오류 또는 에러로 사용이 끝난 자원을 반환하지 못하는 경우이다.

#### 나. 보안대책

자원을 획득하여 사용한 다음에는 반드시 자원을 해제하여 반환한다.

#### 다. 코드예제

try구문 내 처리 중 오류가 발생할 경우, close()메서드가 실행되지 않아 사용한 자원이 반환되지 않을 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
InputStream in = null;
OutputStream out = null;
    try {
    in = new FileInputStream(inputFile);
    out = new FileOutputStream(outputFile);
    ...
    FileCopyUtils.copy(fis, os);
    // 자원반환 실행 전에 오류가 발생할 경우 자원이 반환되지 않으며, 할당된 모든 자원을 반환해야
          한다.
    in.close();
    out.close();
} catch (IOException e) {
     logger.error(e);
}
```

예외상황이 발생하여 함수가 종료될 때, 예외의 발생 여부와 상관없이 항상 실행되는 finally 블록에서 할당받은 모든 자원을 반드시 반환하도록 한다.

**안전한 코드의 예 JAVA**

```java
InputStream in = null;
OutputStream out = null;
    try {
     in = new FileInputStream(inputFile);
     out = new FileOutputStream(outputFile);
     ...
     FileCopyUtils.copy(fis, os);
} catch (IOException e) {
    logger.error(e);
// 항상 수행되는 finally 블록에서 할당받은 모든 자원에 대해 각각 null검사를 수행 후 예외처리를
    하여 자원을 해제하여야 한다.
    } finally {
       if (in != null) {
            try {
                 in.close();
            } catch (IOException e) {
                    logger.error(e);
            }
       }
       if (out != null) {
                try {
                    out.close();
                } catch (IOException e) {
                    logger.error(e);
                }
       }
}
```

파일스트림이 해제되지 않는 C# 코드 예제이다.

**안전하지 않은 코드의 예 C#**

```csharp
public void FileStreamTest()
{
// fsSource에 자원이 할당되었으나 해제되지 않는다.
    FileStream fsSource = new FileStream(pathSource, FileMode.Open, FileAccess.Read);
    byte[] bytes = new byte[fsSource.Length];
    int numBytesToRead = (int)fsSource.Length;
    int numBytesRead = 0;
    while(numBytesToRead > 0)
    {
        int n = fsSource.Read(bytes, numBytesRead, numBytesToRead);
        if(n==0)
          break;
        numBytesToRead += n;
        numBytesToRead -= n;
    }
    using(FileStream fsNew = new FileStream(pathNew, FileMode.Create, FileAccess.Write))
{ /* OK */
     fsNew.Write(bytes, 0, numBytesToRead);
    }
}
```

using 구문을 이용하여 쉽게 자원을 해제할 수 있다.

**안전한 코드의 예 C#**

```csharp
 public void FileStreamTest()
 {
     // using 구문으로 자원을 할당하면 구문이 끝나는 지점에서 자동으로 자원이 해제된다.
      using(FileStream fsSource = new FileStream(pathSource, FileMode.Open,
 FileAccess.Read)){
         byte[] bytes = new byte[fsSource.Length];
         int numBytesToRead = (int)fsSource.Length;
         int numBytesRead = 0;

                                    안전한 코드의 예 C#

        while(numBytesToRead > 0)
        {
            int n = fsSource.Read(bytes, numBytesRead, numBytesToRead);
            if(n==0)
             break;
             numBytesToRead += n;
             numBytesToRead -= n;
        }
    }
    using(FileStream fsNew = new FileStream(pathNew, FileMode.Create,
FileAccess.Write)) { /* OK */
        fsNew.Write(bytes, 0, numBytesToRead);
    }
}
```

아래 C 코드는 파일을 연 상태에서 오류가 발생했을 때 자원 누수가 발생한다.

**안전하지 않은 코드의 예 C**

```c
void ImproperResourceRelease(char* filename) {
        char buf[BUF_SIZE];
        FILE *f = fopen(filename, “r”);
        if(!checkSomething()) {
printf(“Something is wrong”);
        return;
}
// checkSomething에서 false를 반환하는 경우, 파일 핸들러를 종료할 수 없다.
fclose(f);
}
```

오류가 발생한 상황에서도 정상적으로 파일 핸들러를 종료하도록 수정한다.

**안전한 코드의 예 C#**

```csharp
void ImproperResourceRelease(char* filename) {
     char buf[BUF_SIZE];
     FILE *f = fopen(filename, “r”);
     if(!checkSomething()) {
      printf(“Something is wrong”);
     // checkSomthing에서 false를 반환해도 파일 핸들러를 종료하도록 수정
      fclose(f);
     return;
      }
fclose(f);
}
```

#### 라. 참고자료

- ① CWE-404 Improper Resource Shutdown or Release, MITRE, http://cwe.mitre.org/data/definitions/404.html
- ② Release resources when they are no longer needed, CERT, http://www.securecoding.cert.org/confluence/display/java/FIO04-J.+Release+resources+when+they+are+no+longer+needed
- ③ Unreleased Resource, OWASP, https://www.owasp.org/index.php/Unreleased_ Resource
### 3. 해제된 자원 사용

#### 가. 개요

C언어에서 동적 메모리 관리는 보안 취약점을 유발하는 대표적인 프로그램 결함의 원인이다. 해제한 메모리를 참조하게 되면 예상치 못한 값 또는 코드를 실행하게 되어 의도하지 않은 결과가 발생하게 된다.

#### 나. 보안대책

동적으로 할당된 메모리를 해제한 후 그 메모리를 참조하고 있던 포인터를 참조 추적이나 형 변환, 수식에서의 피연산자 등으로 사용하여 해제된 메모리에 접근하도록 해서는 안된다. 또한, 메모리 해제 후, 포인터에 널(Null)값을 저장하거나 다른 적절한 값을 저장하면 의도하지 않은 코드의 실행을 막을 수 있다.

#### 다. 코드예제

다음 예제는 동적 변수 temp에 할당된 동적 메모리를 해제 후 다시 사용하고 있다. 이 경우 예상치 못한 임의의 프로그램이 수행되는 취약점을 유발할 수 있다.

**안전하지 않은 코드의 예 C**

```c
int main(int argc, const char *argv[]) {
     char *temp;
     temp = (char *)malloc(BUFFER_SIZE);
     ……
     free(temp);
     // 해제한 자원을 사용하고 있어 의도하지 않은 결과가 발생하게 된다.
     stmcpy(temp, argv[1], BUFFER_SIZE-1);
}
```

다음 예제와 같이 메모리를 해제하기 전에 할당한 메모리를 사용하는 작업을 수행하고 최종적으로 메모리를 해제한다.

**안전한 코드의 예 C**

```c
int main(int argc,const char *argv[]) {
    char *temp;
    temp = (char *)malloc(BUFFER_SIZE);
    ……
    // 할당된 자원을 최종적으로 사용하고 해제하여야 한다.
    stmcpy(temp,argv[1], BUFFER_SIZE-1);
    free(temp);
}
```

다음은 해제 후 사용과 관련된 안전하지 않은 코드의 예이다. 프로그램에서는 문자형으로 동적 할당된 메모리를 참조하는 포인터와 정수형 변수 data_type을 사용한다. 만일 data_type값이 val_1과 동일하면서 동시에 val_2와도 동일한 값이 된다면, 두 번째 조건문에서 이중 해제 문제가 발생한다.

**안전하지 않은 코드의 예 C**

```c
char *data;
int data_type
if (data_type==val_1) { free(data); }
       ……
// 이미 해제된 자원을 이중 해제하여 문제가 발생한다.
if (data_type==val_2) { free(data); }
```

동적 할당된 포인터를 해제한 후에 NULL값으로 설정함으로써 동일한 메모리 할당에 대해서는 한번만 해제하도록 하여 이중 해제 문제를 방지한다.

**안전한 코드의 예 C**

```c
char *data;
int data_type
if (data_type==val_1) {
     free(data);
    // 메모리를 해제한 후 항상 포인터에 NULL을 할당하여 이중 해제하더라도 무시되게 한다.
     data = NULL;
}
       ……
if (data_type==val_2) {
      free(data);
    // 메모리를 해제한 후 항상 포인터에 NULL을 할당하여 이중 해제하더라도 무시되게 한다.
     data = NULL;
}
```

#### 라. 참고자료

- ① CWE-416, Use After Free, MITRE, http://cwe.mitre.org/data/definitions/416.html
- ② Do not access freed memory, CERT, http://www.securecoding.cert.org/confluence/display/c/MEM30-C.+Do+not+access+freed+memory
- ③ Using freed memory, OWASP, https://www.owasp.org/index.php/Using_freed_memory
### 4. 초기화되지 않은 변수 사용

#### 가. 개요

C 언어의 경우 스택 메모리에 저장되는 지역변수는 생성될 때 자동으로 초기화되지 않는다. 초기화 되지 않은 변수를 사용하게 될 경우 임의값을 사용하게 되어 의도하지 않은 결과를 출력하거나 예상치 못한 동작을 수행할 수 있다.

#### 나. 보안대책

초기화되지 않은 스택 메모리 영역의 변수는 임의값이라 생각해서 대수롭지 않게 생각할 수 있으나 사실은 이전 함수에서 사용되었던 내용을 포함하고 있다. 공격자는 이러한 약점을 사용하여 메모리에 저장되어 있는 값을 읽거나 특정 코드를 실행할 수 있다. 모든 변수를 사용 전에 반드시 올바른 초기값을 할당함으로서 이러한 문제를 예방한다.

#### 다. 코드예제

다음 코드는 커서의 위치를 정하는 프로그램이다. switch문 안에서 초기화를 수행하도록 구현이 되어 있으나, default 부분에서 변수 x만 초기화하고 변수 y는 초기화되지 않았으므로 이 함수가 수행되기 전에 공격자가 이 변수에 원하는 값을 저장해 놓는다면 서비스 거부 공격도 가능하다.

**안전하지 않은 코드의 예 C**

```c
// 변수의 초기값을 지정하지 않을 경우 공격에 사용 될 수 있어 안전하지 않다.
int x, y;
switch(position) {
    case 0: x = base_position; y = base_position beak;
    case 1: x = base_position + i; y = base_position - i break;
    default: x=1; break;
}
setCursorPosition(x,y);
```

아래의 예제는 switch 문 안에 case 항목으로 존재하던 초기화 구문을 switch문 밖으로 꺼내어 변수를 올바르게 초기화 하고 있으므로 안전하다.

**안전한 코드의 예 C**

```c
// 변수의 초기값은 항상 지정하여야 한다.
int x=1, y=1;
switch(position) {
     case 0: x = base_position; y = base_position beak;
     case 1: x = base_position + i; y = base_position - i break;
     default: x=1; break;
}
setCursorPosition(x,y);
```

#### 라. 참고자료

- ① CWE-457, Use of Uninitialized Variable, MITRE, http://cwe.mitre.org/data/definitions/457.html
- ② Do not read uninitialized memory, CERT, http://www.securecoding.cert.org/confluence/display/c/EXP33-C.+Do+not+read+uninitialized+memory
- ③ Uninitialized Variable, OWASP, https://www.owasp.org/index.php/Uninitialized_variable
### 5. 신뢰할 수 없는 데이터의 역직렬화

#### 가. 개요

직렬화(Serialization)는 프로그램에서 특정 클래스의 현재 인스턴스 상태를 다른 서버로 전달하기 위해 클래스의 인스턴스 정보를 바이트 스트림으로 복사하는 작업으로, 메모리 상에서 실행되고 있는 객체의 상태를 그대로 복제하여 파일로 저장하거나 수신 측에 전달하게 된다.

역직렬화(Deserialization)는 반대 연산으로 바이너리 파일이나 바이트 스트림으로부터 객체 구조로복원하게 된다.

이 때, 송신자가 네트워크를 이용하여 직렬화된 정보를 수신자에게 전달하는 과정에서 공격자가 전송또는 저장된 스트림을 조작할 수 있는 경우에는 신뢰할 수 없는 역직렬화를 이용하여 무결성 침해, 원격 코드 실행, 서비스 거부 공격 등이 발생 할 수 있는 보안약점이다.

#### 나. 보안대책

초기화되지 않은 스택 메모리 영역의 변수는 임의값이라 생각해서 대수롭지 않게 생각할 수 있으나사실은 이전 함수에서 사용되었던 내용을 포함하고 있다. 공격자는 이러한 약점을 사용하여 메모리에저장되어 있는 값을 읽거나 특정 코드를 실행할 수 있다. 모든 변수를 사용 전에 반드시 올바른 초기값을 할당함으로서 이러한 문제를 예방한다.

신뢰할 수 없는 데이터를 역직렬화 하지 않도록 응용프로그램을 구성한다. 민감정보 또는 중요정보를 전송 시 암호화 통신을 적용하지 못하는 경우, 송신 측에서 서명을 추가하고 수신 측에서 서명을 확인하여 데이터의 무결성을 검증한다.

또는, 신뢰할 수 있는 데이터의 식별을 위해 역직렬화 대상의 데이터가 사전에 검증된 클래스만을 포함하는지 검증하거나, 제한된 실행 권한을 구성하여 역직렬화 코드를 실행한다.

#### 다. 코드예제

다음 예제는 맵(map)을 직렬화하고 역직렬화 하는 코드이다. 데이터를 전송할 경우 공격자가 바이트스트림을 조작하여 역직렬화 공격이 가능한 객체를 생성할 수 있는 예제이다.

**안전하지 않은 코드의 예 JAVA**

```java
public static void main(String[] args) throws
IOException, GeneralSecurityException, ClassNotFoundException {
       ....
       // map을 역직렬화 한다.
       ObjectInputStream in = new ObjectInputStream(new FileInputStream("data"));
       sealedMap = (SealedObject) in.readObject();
       in.close();

       // 객체를 추출한다.
       cipher = Cipher.getInstance("AES");
       cipher.init(Cipher.DECRYPT_MODE, key);
       signedMap = (SignedObject) sealedMap.getObject(cipher);

       // 서명값 검증 과정에서 불일치 시 예외를 리턴하고, 일치 시 map 값을 읽는다.
       if (!signedMap.verify(kp.getPublic(), sig)) {
       throw new GeneralSecurityException("Map failed verification");
       }
       map = (SerializableMap<String, Integer>) signedMap.getObject();
}
```

다음 예제는 서명 값을 검증하여 메시지 위변조를 방지할 수 있는 코드이다.

**안전한 코드의 예 JAVA**

```java
public static void main(String[] args) throws
IOException, GeneralSecurityException, ClassNotFoundException {
       ....
       // map을 역직렬화 한다.
       ObjectInputStream in = new ObjectInputStream(new FileInputStream("data"));
       sealedMap = (SealedObject) in.readObject();
       in.close();

       // 객체를 추출한다.
       cipher = Cipher.getInstance("AES");

                                 안전한 코드의 예 JAVA

        cipher.init(Cipher.DECRYPT_MODE, key);
        signedMap = (SignedObject) sealedMap.getObject(cipher);
        // 서명값 검증 과정에서 불일치 시 예외를 리턴하고, 일치 시 map 값을 읽는다.
              if (!signedMap.verify(kp.getPublic(), sig)) {
                       throw new GeneralSecurityException("Map failed verification");
              }
              map = (SerializableMap<String, Integer>) signedMap.getObject();
 }
```

다음 예제는 바이트 배열의 입력 값을 검증 없이 readObject()로 역직렬화하여 악의적인 코드가 실행될 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
class DeserializeExample {
       public static Object deserialize(byte[] buffer)
       throws IOException, ClassNotFoundException {
             Object ret = null;
             try (ByteArrayInputStream bais = new ByteArrayInputStream(buffer)) {
                      try (ObjectInputStream ois = new ObjectInputStream(bais)) {
                               ret = ois.readObject();
                      }
             }
       return ret;
       }
}
```

이를 안전한 코드로 변환하기 위해서는 ObjectInputStream을 상속 받아Whitelisted Object InputStream 객체를 구현하여 사용한다. WhitelistedObjectInputStream에서는 readObject()를 실행 시, resolveClass 함수를 호출하여 설정한 화이트리스트와 비교하여 리스트에 없는 데이터일 경우 예외를 발생시킨다.

**안전한 코드의 예 JAVA**

```java
```

public class WhitelistedObjectInputStream extends ObjectInputStream { public Set<String> whitelist; // WhilelistedObjectInputStream을 생성할 때 화이트리스트를 입력받는다. public WhitelistedObjectInputStream(InputStream inputStream, Set<String> wl) throws IOException { super(inputStream); whitelist = wl; }

@Override protected Class<?> resolveClass(ObjectStreamClass cls) throws IOException, ClassNotFoundException { // ObjectStreamClass의 클래스명이 화이트리스트에 있는지 확인한다. if (!whitelist.contains(cls.getName())) { throw new InvalidClassException("Unexpected serialized class", cls.getName()); } return super.resolveClass(cls); } }

@RequestMapping(value = "/upload", method = RequestMethod.POST) public Student upload(@RequestParam("file") MultipartFile multipartFile) throws ClassNotFoundException, IOException { Student student = null; File targetFile = new File("/temp/" + multipartFile.getOriginalFilename()); // 역직렬화 대상 클래스 이름의 화이트리스트 생성한다. Set<String> whitelist = new HashSet<String>(Arrays.asList( new String[] { "Student" })); try (InputStream fileStream = multipartFile.getInputStream()) { try (WhitelistedObjectInputStream ois = new WhitelistedObjectInputStream(fileStream, whitelist)) { // 화이트리스트에 없는 역직렬화 데이터의 경우 예외 발생시킨다. student = (Student) ois.readObject(); } } return student; }

#### 라. 참고자료

- ① CWE-502 Deserialization of Untrusted Data, MITRE, https://cwe.mitre.org/data/definitions/502.html
## 제6절 캡슐화

중요한 데이터 또는 기능성을 불충분하게 캡슐화하거나 잘못 사용함으로써 발생하는 보안약점으로 정보노출, 권한문제 등이 발생할 수 있다.

### 1. 잘못된 세션에 의한 데이터 정보노출

#### 가. 개요

다중 스레드 환경에서는 싱글톤(Singleton)8 객체 필드에 경쟁조건(Race Condition)이 발생할 수 있다. 따라서, 다중 스레드 환경인 Java의 서블릿(Servlet) 등에서는 정보를 저장하는 멤버 변수가 포함되지 않도록 하여, 서로 다른 세션에서 데이터를 공유하지 않도록 해야 한다.

#### 나. 보안대책

싱글톤 패턴을 사용하는 경우, 변수 범위(Scope)에 주의를 기울여야 한다. 특히 Java에서는 HttpServlet 클래스의 하위클래스에서 멤버 필드를 선언하지 않도록 하고, 필요한 경우 지역 변수를 선언하여 사용한다.

#### 다. 코드예제

JSP 선언부(<%! 소스코드 %>)에 선언한 변수는 해당 JSP에 접근하는 모든 사용자에게 공유된다. 먼저 호출한 사용자가 값을 설정하고 사용하기 전에 다른 사용자의 호출이 발생하게 되면, 뒤에 호출한 사용자가 설정한 값이 모든 사용자에게 적용되게 된다.

> <sup>8</sup> 싱글톤 패턴 : GOF 32가지 패턴 중 하나. 하나의 프로그램 내에서 하나의 인스턴스만을 생성해야만 하는 패턴. Connection Pool, Thread Pool과 같이 Pool 형태로 관리되는 클래스의 경우 프로그램 내에서 단하나의 인스턴트로 관리해야 하는 경우를 말함. java에서는 객체로 제공됨

**안전하지 않은 코드의 예 JAVA**

```java
<%@page import="javax.xml.namespace.*"%>
<%@page import="gov.mogaha.ntis.web.frs.gis.cmm.util.*" %>
<%!
      // JSP에서 String 필드들이 멤버 변수로 선언됨
      String username = "/";
      String imagePath = commonPath + "img/";
      String imagePath_gis = imagePath + "gis/cmm/btn/";
……
%>
```

JSP의 서블릿(<% 소스코드 %>)에 정의한 변수는 _jspService 메소드의 지역변수로 선언되므로 공유가 발생하지 않아 안전하다.

**안전한 코드의 예 JAVA**

```java
<%@page import="javax.xml.namespace.*"%>
<%@page import="gov.mogaha.ntis.web.frs.gis.cmm.util.*" %>
<%
      // JSP에서 String 필드들이 로컬 변수로 선언됨
      String commonPath = "/";
      String imagePath = commonPath + "img/";
      String imagePath_gis = imagePath + "gis/cmm/btn/";
      ……
%>
```

Controller에 멤버 변수를 사용하면 공유가 발생하여 동기화 오류가 발생할 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
 @Controller
 public class TrendForecastController {
      // Controller에서 int 필드가 멤버 변수로 선언되어 스레드간에 공유됨

                           안전하지 않은 코드의 예 JAVA

  private int currentPage = 1;
  public void doSomething(HttpServletRequest request) {
      currentPage = Integer.parseInt(request.getParameter("page"));
  }
……
```

Controller에 멤버 변수를 사용하지 않고 지역변수로 사용한다.

**안전한 코드의 예 JAVA**

```java
@Controller
public class TrendForecastController {
   public void doSomething(HttpServletRequest request) {
   // 지역변수로 사용하여 스레드간 공유되지 못하도록 한다.
   int currentPage = Integer.parseInt(request.getParameter("page"));
   }

……
```

다중 스레드 환경에서 IHttpHandler 클래스에 정보를 저장하는 필드가 포함되서는 안된다.

**안전하지 않은 코드의 예 C#**

```csharp
class DataLeakBetweenSessions : IHttpHandler
  {
      // 다중 스레드 환경에서 IHttpHandler 를 구현하는 클래스에 정보를 저장하는 필드가 포함되면
         안된다.
      private String id;
      public void ProcessRequest(HttpContext ctx)
      {
var json = new JSONResonse()
       {
           Success = ctx.Request.QueryString["name"] != null,
           Name = ctx.Request.QueryString["name"]

                                           안전하지 않은 코드의 예 C#

              };
                  ctx.Response.ContentType = "application/json";
                  ctx.Response.Write(JsonConvert.SerializeObject(json));
          }
          public bool IsReusable
          {
                  get { return false; }
          }
  }
```

해당 내용을 지역변수나 세션변수를 이용하여 처리하여야 한다.

**안전한 코드의 예 C#**

```csharp
class DataLeakBetweenSessions : IHttpHandler
     {
         public void ProcessRequest(HttpContext ctx)
         {
// 지역변수나 세션변수를 선언해서 사용해야한다.
     ctx.Session["id"] = ctx.Request.QueryString["id"];
                         ctx.Response.ContentType = "application/json";
                         ctx.Response.Write(JsonConvert.SerializeObject(json));
                     }
                     public bool IsReusable
                     {
                         get { return false; }
                     }
             }

                 var json = new JSONResonse()
                 {
                         Success = ctx.Request.QueryString["name"] != null,
                         Name = ctx.Request.QueryString["name"]
                 };
```

#### 라. 참고자료

- ① CWE-488 Exposure of Data Element to Wrong Session, MITRE, http://cwe.mitre.org/data/definitions/488.html
- ② CWE-543 Use of Singleton Pattern Without Synchronization in a Mulitithreaded Context, MITRE, http://cwe.mitre.org/data/definitions/543.html
- ③ Do not let session information leak within a servlet, CERT, http://www.securecoding.cert.org/confluence/display/java/MSC11-J.+Do+not+let+session+information+leak+within+a+servlet
### 2. 제거되지 않고 남은 디버그 코드

#### 가. 개요

디버깅 목적으로 삽입된 코드는 개발이 완료되면 제거해야 한다. 디버그 코드는 설정 등의 민감한 정보를 담거나 시스템을 제어하게 허용하는 부분을 담고 있을 수 있다. 만일, 남겨진 채로 배포될 경우, 공격자가 식별 과정을 우회하거나 의도하지 않은 정보와 제어 정보가 노출될 수 있다.

#### 나. 보안대책

소프트웨어 배포 전, 반드시 디버그 코드를 확인 및 삭제한다. 일반적으로 Java 개발자의 경우 웹응용프로그램을 제작할 때 디버그용도의 코드를 main()에 개발한 후 이를 삭제하지 않는 경우가 많다.디버깅이 끝나면 main() 메소드를 삭제해야 한다.

#### 다. 코드예제

다음의 예제는 main() 메소드 내에 화면에 출력하는 디버깅 코드를 포함하고 있다. J2EE의 경우 main() 메소드 사용이 필요 없으며, 개발자들이 콘솔 응용프로그램으로 화면에 디버깅코드를 사용하는 경우가 일반적이다.

**안전하지 않은 코드의 예 JAVA**

```java
class Base64 {
    public static void main(String[] args) {
        if (debug) {
            byte[] a = { (byte) 0xfc, (byte) 0x0f, (byte) 0xc0 };
             byte[] b = { (byte) 0x03, (byte) 0xf0, (byte) 0x3f };
             ……
         }
    }
        public void otherMethod() { … }
}
```

이에 따라 J2EE와 같은 응용프로그램에서 main() 메소드는 삭제한다. J2EE의 main() 메소드의 경우 디버깅 코드인 경우가 일반적이다.

**안전한 코드의 예 JAVA**

```java
class Base64 {
         public void otherMethod() { … }
}
```

디버그용 코드가 남아있는 C# 코드의 예제이다.

**안전하지 않은 코드의 예 C#**

```csharp
class Example {
    public void Log() {
         // Console.WriteLine 등의 메소드를 사용한 디버그용 코드가 남아있다.
        Console.WriteLine("sensitive info");
    }
}
```

디버그용 코드를 삭제 하여야 한다.

**안전한 코드의 예 C#**

```csharp
class Example {
         public void Log() {
         // 디버그용 코드를 삭제해야한다.
        //Console.WriteLine("sensitive info");
    }
}
```

아래는 디버그용 코드가 남아있는 C 코드의 예제이다. 공격자가 출력되는 콜 스택으로 프로그램 구조를 유추할 수 있다.

**안전하지 않은 코드의 예 C**

```c
void LeftoverDebugCode() {
      int i, ntprs;
      char **strings;
      nptrs = backtrace(buffer, 100);
      strings = backtrace_symbols(buffer, nptrs);
      …
      // 디버그 모드일 시 콜스택을 출력한다.
      if(debug) {
      for(i=0; i < nptr; i++) printf(“%s\n”, strings[j]);
      }
}
```

릴리즈 시에는 디버그용 코드를 삭제 하여야 한다.

**안전한 코드의 예 C**

```c
void LeftoverDebugCode() {
      … // 디버그 코드를 삭제하고 동작 코드만 남긴다.
}
```

#### 라. 참고자료

- ① CWE-489 Leftover Debug Code, MITRE, http://cwe.mitre.org/data/definitions/489.html
- ② Production code must not contain debugging entry points, CERT, http://www.securecoding.cert.org/confluence/display/java/ENV06-J.+Production+code+must+not+contain+debugging+entry+points
### 3. Public 메소드부터 반환된 Private 배열

#### 가. 개요

private로 선언된 배열을 public으로 선언된 메소드로 반환(return)하면, 그 배열의 레퍼런스가 외부에 공개되어 외부에서 배열수정과 객체 속성변경이 가능해진다.

#### 나. 보안대책

private로 선언된 배열을 public으로 선언된 메소드로 반환하지 않도록 해야 한다. private 배열에 대한 복사본을 반환하도록 하고 배열의 원소에 대해서는 clone() 메소드로 복사된 원소를 저장하도록 하여 private 선언된 배열과 객체속성에 대한 의도하지 않게 수정되는 것을 방지한다. 만약 배열의 원소가 String 타입 등과 같이 변경이 되지 않는 경우에는 Private 배열의 복사본을 만들고 이를 반환하도록 작성한다.

#### 다. 코드예제

멤버 변수 colors는 private로 선언되었지만 public으로 선언된 getColors() 메소드로 참조를 얻을 수 있다. 이 경우 의도하지 않은 수정이 발생할 수 있다.

아래의 코드는 멤버 변수 colors는 private로 선언되었지만 public으로 선언된 getUserColors 메소드로 private 배열에 대한 reference를 얻을 수 있다. 이 경우 의도하지 않은 수정이 발생할 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
// private 인 배열을 public인 메소드가 return한다.
private Color[] colors;
public Color[] getUserColors(Color[] userColors) { return colors; }
```

private배열에 대한 복사본을 만들고, 복사된 배열의 원소로는 clone() 메소드로 private 배열의 원소의 복사본을 만들어 저장하여 반환하도록 작성하면, private선언된 배열과 원소에 대한 의도하지 않은 수정을 방지할 수 있다.

**안전한 코드의 예 JAVA (배열의 원소가 일반객체일 경우)**

```text
private Color[] colors;
// 메소드를 private으로 하거나, 복제본 반환, 수정하는 public 메소드를 별도로 만든다.
public void onCreate(Bundle savedInstanceState) {
super.onCreate(savedInstanceState);
Color[] newColors = getUserColors();
     ......
}
public Color[] getUserColors(Color[] userColors) {
    // 배열을 복사한다.
Color[] colors = new Color [userColors.length];
for (int i = 0; i < colors.length; i++)
// clone()메소드를 이용하여 배열의 원소도 복사한다.
colors[i] = this.colors[i].clone();
return colors;
}
```

아래의 코드는 멤버 변수 colors는 private로 선언되었지만, public으로 선언된 getColors() 메소드로 reference를 얻을 수 있다. 이 경우 의도하지 않은 배열의 수정이 발생할 수 있다.

안전하지 않은 코드의 예 JAVA (배열의 원소가 String 타입 등과 같이 수정이 되지 않는 경우)

// private 인 배열을 public인 메소드가 return한다. private String[] colors; public String[] getColors() { return colors; }

private배열의 복사본을 만들고, 이를 반환하도록 작성하면, private 선언된 배열에 대한 의도하지 않은 수정을 방지할 수 있다.

안전한 코드의 예 JAVA (배열의 원소가 String 타입 등과 같이 수정이 되지 않는 경우)

private String[] colors; // 메소드를 private으로 하거나, 복제본 반환, 수정하는 public 메소드를 별도로 만든다. public void onCreate(Bundle savedInstanceState) { super.onCreate(savedInstanceState); String[] newColors = getColors(); ...... } public String[] getColors() { String[] ret = null; if ( this.colors != null ) { ret = new String[colors.length]; for (int i = 0; i < colors.length; i++) { ret[i] = this.colors[i]; } } return ret; }

아래의 코드는 멤버 변수 colors는 private로 선언되었지만 public으로 선언된 getUserColors 메소드로 private 배열에 대한 reference를 얻을 수 있다. 이 경우 의도하지 않은 수정이 발생할 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
// private 인 collection을 public인 메소드가 return한다.
private List<Color> colors;
public List<Color> getUserColors() { return colors; }
```

메소드를 private 으로 하거나, 복제본 반환, 수정하는 public 메소드를 별도로 만들어야 한다.

**안전한 코드의 예 C#**

```csharp
private List<Color> colors;
// 메소드를 private으로 하거나, 복제본 반환, 수정하는 public 메소드를 별도로 만든다.

public List<Color> getUserColors() {
 // 배열을 복사한다.
List< ICloneable> newList = new List< ICloneable>(colors.Count);
//Clone()메소드를 이용하여 collection의 원소도 복사한다.
colors.ForEach((item) =>
{
    newList.Add((ICloneable)item.Clone());
});
return newList;
}
```

#### 라. 참고자료

- ① CWE-495 Private Array-Typed Field Returned From A Public Method, MITRE, http://cwe.mitre.org/data/definitions/495.html
- ② Do not return references to private mutable class members, CERT, http://www.securecoding.cert.org/confluence/display/java/OBJ05-J.+Do+not+return+references+to+private+mutable+class+members
### 4. Private 배열에 Public 데이터 할당

#### 가. 개요

public으로 선언된 메소드의 인자가 private선언된 배열에 저장되면, private배열을 외부에서 접근하여 배열수정과 객체 속성변경이 가능해진다.

#### 나. 보안대책

public으로 선언된 메서드의 인자를 private선언된 배열로 저장되지 않도록 한다. 인자로 들어온 배열의 복사본을 생성하고 clone() 메소드로 복사된 원소를 저장하도록 하여 private변수에 할당하여 private선언된 배열과 객체속성에 대한 의도하지 않게 수정되는 것을 방지한다. 만약 배열 객체의 원소가 String 타입 등과 같이 변경이 되지 않는 경우에는 인자로 들어온 배열의 복사본을 생성하여 할당한다.

#### 다. 코드예제

아래의 코드는 멤버 변수 userRoles는 private로 선언되었지만 public으로 선언된 setUserRoles 메소드로 인자가 할당되어 배열의 원소를 외부에서 변경할 수 있다. 이 경우 의도하지 않은 배열과 원소에 대한 객체속성 수정이 발생할 수 있다.

**안전하지 않은 코드의 예 JAVA (배열의 원소가 일반객체일 경우)**

```text
// userRoles 필드는 private이지만, public인 setUserRoles()로 외부의 배열이 할당되면,
   사실상 public 필드가 된다.
private UserRole[] userRoles;
public void setUserRoles(UserRole[] userRoles) {
this.userRoles = userRoles;
}
```

인자로 들어온 배열의 복사본을 생성하고 clone() 메소드로 복사된 원소를 저장하도록 하여 private변수에 할당하면 private으로 할당된 배열과 원소에 대한 의도하지 않은 수정을 방지할 수 있다.

**안전한 코드의 예 JAVA (배열의 원소가 일반객체일 경우)**

```text
// 객체가 클래스의 private member를 수정하지 않도록 한다.
private UserRole[] userRoles;
public void setUserRoles(UserRole[] userRoles) {
this.userRoles = new UserRole[userRoles.length];
for (int i = 0; i < userRoles.length; ++i)
this.userRoles[i] = userRoles[i].clone();
}
```

아래의 코드는 멤버 변수 userRoles는 private로 선언되었지만 public으로 선언된 setUserRoles 메소드로 인자가 할당되어 배열의 원소를 외부에서 변경할 수 있다. 이 경우 의도하지 않은 배열에 대한수정이 발생할 수 있다.

안전하지 않은 코드의 예 JAVA (배열의 원소가 String 타입 등과 같이 수정이 되지 않는 경우)

// userRoles 필드는 private이지만, public인 setUserRoles()로 외부의 배열이 할당되면, 사실상 public 필드가 된다. private String[] userRoles; public void setUserRoles(String[] userRoles) { this.userRoles = userRoles; }

인자로 들어온 배열의 복사본을 생성하여 private변수에 할당하면 private으로 할당된 배열에 대한 의도하지 않은 수정을 방지할 수 있다.

**안전한 코드의 예 (배열의 원소가 String 타입 등과 같이 수정이 되지 않는 경우)**

```text
// 객체가 클래스의 private member를 수정하지 않도록 한다.
private String[] userRoles;

public void setUserRoles(String[] userRoles) {
    this.userRoles = new String[userRoles.length];
    for (int i = 0; i < userRoles.length; ++i)
    this.userRoles[i] = userRoles[i];
}
```

아래의 코드는 멤버 변수 userRoles는 private로 선언되었지만 public으로 선언된 setUserRoles 메소드로 인자가 할당되어 배열의 원소를 외부에서 변경할 수 있다. 이 경우 의도하지 않은 배열과 원소에 대한 객체속성 수정이 발생할 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
class Program
    {
// userRoles 필드는 private이지만, public인 setUserRoles()으로 외부의 배열이 할당되면,
     사실상 public 필드가 된다.
       private String[] userRoles;
          public void SetUserRoles(String[] userRoles)
          {
              this.userRoles = userRoles;
          }

      }
```

객체가 클래스의 private member를 수정하지 않도록 하여야 한다.

**안전한 코드의 예 C#**

```csharp
class Program
    {
// 객체가 클래스의 private member를 수정하지 않도록 한다.
        private String[] userRoles;
        public void SetUserRoles(String[] userRoles)
        {
            int length = userRoles.Length;
            this.userRoles = new String[length];
            for(int i = 0; i < length; i++) { \
                this.userRoles[i] = userRoles[i];
            }
        }
    }
```

#### 라. 참고자료

- ① CWE-496 Public Data Assigned to Private Array-Typed Field, MITRE, http://cwe.mitre.org/data/definitions/496.html
## 제7절 API 오용

의도된 사용에 반하는 방법으로 API를 사용하거나, 보안에 취약한 API를 사용하여 발생할 수 있는 보안약점이다.

### 1. DNS lookup에 의존한 보안결정

#### 가. 개요

공격자가 DNS 엔트리를 속일 수 있으므로 도메인명에 의존에서 보안결정(인증 및 접근 통제 등)을 하지 않아야 한다. 만약, 로컬 DNS 서버의 캐시가 공격자에 의해 오염된 상황이라면, 사용자와 특정 서버 간의 네트워크 트래픽이 공격자를 경유하도록 할 수도 있다. 또한, 공격자가 마치 동일 도메인에 속한 서버인 것처럼 위장할 수도 있다.

#### 나. 보안대책

보안결정에서 도메인명을 이용한 DNS lookup을 하지 않도록 한다.

#### 다. 코드예제

다음의 예제는 도메인명으로 해당 요청을 신뢰할 수 있는지를 검사한다. 그러나 공격자는 DNS 캐쉬 등을 조작해서 쉽게 이러한 보안 설정을 우회할 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
 public void doGet(HttpServletRequest req, HttpServletResponse res)
    throws ServletException, IOException {
    boolean trusted = false;
    String ip = req.getRemoteAddr();
    InetAddress addr = InetAddress.getByName(ip);
// 도메인은 공격자에 의해 실행되는 서버의 DNS가 변경될 수 있으므로 안전하지 않다.

                           안전하지 않은 코드의 예 JAVA

    if (addr.getCanonicalHostName().endsWith("trustme.com")) {
         do_something_for_Trust_System();
    }
```

그러므로, 다음의 예제와 같이 DNS lookup에 의한 호스트 이름 비교를 하지 않고, IP 주소를 직접 비교하도록 수정한다.

**안전한 코드의 예 JAVA**

```java
public void doGet(HttpServletRequest req, HttpServletResponse res)
    throws ServletException, IOException {
    String ip = req.getRemoteAddr();
    if (ip == null || "".equals(ip)) return ;
// 이용하려는 실제 서버의 IP 주소를 사용하여 DNS변조에 방어한다.
    String trustedAddr = "127.0.0.1";
    if (ip.equals(trustedAddr)) {
         do_something_for_Trust_System();
    }
```

다음의 예제는 도메인명으로 해당 요청을 신뢰할 수 있는지를 검사한다. 그러나 공격자는 DNS 캐시 등을 조작해서 쉽게 이러한 보안 설정을 우회할 수 있다.

**안전하지 않은 코드의 예 C#**

```csharp
bool trusted;
string remoteIpAddress = Request.ServerVariables["REMOTE_HOST"];
IPAddress hostIPAddress = IPAddress.Parse(remoteIpAddress);
IPHostEntry hostInfo = Dns.GetHostByAddress(hostIPAddress);
string hostName = hostInfo.HostName;
if (hostName.EndsWith("trust.com"))
{
trusted = true;
}
```

IP주소를 직접 비교하도록 한다.

**안전한 코드의 예 C#**

```csharp
bool trusted;
string remoteIpAddress = Request.ServerVariables["REMOTE_HOST"];

if ( remoteIpAddress.Equals(trustedAddr))
{
     trusted = true;
     Do_something_for_Trust_System();
}
```

아래 C 코드는 요청의 신뢰성을 호스트의 이름으로 판별하고 있다. 공격자는 DNS 캐시를 조작하여 보안 정책을 우회할 수 있다.

**안전하지 않은 코드의 예 C**

```c
struct hostent *hp;struct in_addr myaddr;
char* tHost = "trustme.example.com";
myaddr.s_addr=inet_addr(ip_addr_string);

hp = gethostbyaddr((char *) &myaddr, sizeof(struct in_addr), AF_INET);
// 요청의 신뢰성을 호스트의 이름으로 판별하고 있다.
if (hp && !strncmp(hp->h_name, tHost, sizeof(tHost))) {

     trusted = true;
} else {
    trusted = false;
}
```

다음의 C 코드는 IP 주소를 직접 비교하여 DNS 캐시 조작에 대해 안전하다.

**안전한 코드의 예 C**

```c
 struct hostent *hp;struct in_addr myaddr;
    char* tHost = "127.0.0.1";
       myaddr.s_addr=inet_addr(ip_addr_string);

    hp = gethostbyaddr((char *) &myaddr, sizeof(struct in_addr), AF_INET);
// 호스트의 이름이 아니라 IP로 직접 비교한다.
    if (hp && !strncmp(hp->h_name, tHost, sizeof(tHost))) {
      trusted = true;
      } else {
      trusted = false;
}
```

#### 라. 참고자료

- ① CWE-350 Reliance on Reverse DNS Resolution for a Security-Critical Action, MITRE, http://cwe.mitre.org/data/definitions/350.html
- ② CWE-247 Reliance on DNS Lookups in a Security Decision, MITRE, http://cwe.mitre.org/data/definitions/247.html
### 2. 취약한 API 사용

#### 가. 개요

취약한 API는 보안상 금지된(banned) 함수이거나, 부주의하게 사용될 가능성이 많은 API를 의미한다. 이들 범주의 API에 대해 확인하지 않고 사용할 때 보안 문제를 발생시킬 수 있다. 금지된 API의 대표적인 예로는 스트링 자료와 관련된 gets(), strcat(), strcpy(), strncat(), strncpy(), sprintf() 등이 있다. 또한 보안상 문제가 없다 하더라도 잘못된 방식으로 함수를 사용할 때도 역시 보안 문제를 발생시킬 수 있다.

#### 나. 보안대책

보안 문제로 인해 금지된 함수는 이를 대체할 수 있는 안전한 함수를 사용한다. 그 예로, 위에 언급된 API 대신에 gets_s()/fgets(), strcat_s(), strcpy_s(), strncat_s(), strncpy_s(), sprintf_s()과 같은 안전한 함수를 사용하는 것이 권장된다. 또한 금지된 API는 아니지만 취약한 API의 예시로, 문자열을 정수로 변환할 때 사용하는 strtol()과 같은 함수는 작은 크기의 부호 있는 정수인 int, short, char와 같은 자료형 변환에 사용하면 범위 제한 없이 값을 평가할 수 있다.

취약한 API의 분류는 일반적인 것은 아니지만 개발 조직에 따라 이를 명시한 경우가 있다면7) 반드시 준수한다.

#### 다. 코드예제

아래 예제에서 gets() 함수는 크기와 상관없이 입력값을 버퍼에 저장하기 때문에 버퍼 오버플로우를 유발할 수 있다.

**안전하지 않은 코드의 예 C**

```c
#include <stdio.h>

void requestString()
{
char str[100];
  // gets() 함수는 문자열 길이를 제한 할 수 없어 안전하지 않다.
  gets(str);
}
```

아래 예제와 같이 gets_s() 또는 fgets()함수를 사용하여 입력값의 크기를 제한하여 사용해야 한다.

**안전한 코드의 예 C**

```c
#include <stdio.h>

void requestString()
{
    char str[100];
    // gets_s() 함수는 문자열 길이 제한이 가능하다.
    gets_s(str, sizeof(str));
}
```

다음 예제는 J2EE 응용 프로그램에서 프레임워크 메소드 호출 대신에 소켓을 직접 사용하고 있어, 프레임워크에서 제공하는 보안기능을 제공받지 못한다.

**안전하지 않은 코드의 예 JAVA**

```java
public class S246 extends javax.servlet.http.HttpServlet {
   private Socket socket
  protected void doGet(HttpServletRequest request,
HttpServletResponse response) throws ServletException {
       try {
// 프레임워크의 메소드 호출 대신 소켓을 직접 사용하고 있어 프레임워크에서 제공하는 보안기능을
   제공 받지 못해 안전하지 않다.
socket = new Socket("kisa.or.kr", 8080);
       } catch (UnknownHostException e) {
                      ......
```

타겟이 WAS로 작성될 경우 아래의 코드처럼 보안기능을 제공하는 프레임워크 메소드인 URL Connection 을 이용하여야한다.

**안전한 코드의 예 JAVA**

```java
public class S246 extends javax.servlet.http.HttpServlet {
   protected void doGet(HttpServletRequest request,
      HttpServletResponse response) throws ServletException {
      ObjectOutputStream oos = null;
      ObjectInputStream ois = null;
      try {
              URL url = new URL("http://127.0.0.1:8080/DataServlet");
      // 보안기능을 제공하는 프레임워크의 메소드를 사용하여야한다.
              URLConnection urlConn = url.openConnection();
              urlConn.setDoOutput(true);
                     .......
```

아래 예제는 J2EE 프로그램에서 System.exit()를 사용하고 있다. System.exit() 메소드를 호출 하는 경우 웹 애플리케이션을 실행하고 있는 컨테이너를 종료할 수 있다.

**안전하지 않은 코드의 예 JAVA**

```java
public class U382 extends HttpServlet {
public void doPost(HttpServletRequest request, HttpServletResponse response)
      throws ServletException, IOException {
      try {
              do_something(logger);
} catch (IOException ase) {
           logger.info("ERROR");
   // J2EE 프로그램에서 System.exit()을 사용하여 서비스가 종료 될 수 있다.
              System.exit(1);
      }
```

서비스 종료를 막기 위해, J2EE 프로그램에서는 System.exit() 메소드를 사용하지 않는다.

**안전한 코드의 예 JAVA**

```java
public class U382 extends HttpServlet {
    public void doPost(HttpServletRequest request, HttpServletResponse response)
          throws ServletException, IOException {
          try {
                  do_something(logger);
          } catch (IOException ase) {
              logger.info("ERROR");
          // 서비스 종료를 막기 위해 J2EE에서는 System.exit()를 사용하지 않는다.
          }
```

C# 코드에서 Application.Exit() 을 사용하면 일부 이벤트가 처리되지 않습니다.

**안전하지 않은 코드의 예 C#**

```csharp
try {
    ...
} catch (Exception e) {
  ...
// Application.Exit() 은 즉시 프로그램을 종료하기 때문에, Form.Closed 혹은 Form.Closing
  이벤트가 처리되지 않는다.
Application.Exit();
}
```

이벤트 처리를 위해 Application.Exit()을 사용하지 않습니다.

**안전한 코드의 예 C#**

```csharp
try {
    ...
} catch (Exception e) {
    ...
// Application.Exit() 을 사용하지 않으면, 이벤트를 처리하지 못하고 프로그램이 종료되는 것을
     방지할 수 있다.
    this.Close();
}
```

#### 라. 참고자료

- ① CWE-676 Use of Potentially Dangerous Function, MITRE, http://cwe.mitre.org/data/definitions/676.html
- ② CWE-242 Use of Inherently Dangerous Function, MITRE, http://cwe.mitre.org/data/definitions/242.html
- ③ CWE-246 J2EE Bad Practices: Direct Use of Sockets, MITRE, http://cwe.mitre.org/data/definitions/246.html
- ④ CWE-382 J2EE Bad Practices: Use of System.exit(), MITRE, http://cwe.mitre.org/data/definitions/382.html
- ⑤ Do not use deprecated or obsolescent functions, CERT, http://www.securecoding.cert.org/confluence/display/c/MSC24-C.+Do+not+use+deprecated+or+obsolescent+ functions

---

**이전**: [제3장 분석·설계단계 보안강화 활동](03-analysis-design-phase.md) | **다음**: [제5장 부록](05-appendix.md)
