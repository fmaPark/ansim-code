---
type: Standard
title: TTAK.KO-11.0309/R1 — 오픈소스 소프트웨어 공급망 관리를 위한 소프트웨어 구성요소 목록(SBOM) 속성 규격
description: SBOM에 포함해야 할 15가지 표준 속성과 속성별 확인 절차를 정의한 TTA 표준의 마크다운 변환본.
resource: TTAK.KO-11.0309/R1
status: stable
tags: [tta-standard, sbom, 속성규격]
generated: { by: "human:개발-풀스택", at: "2026-08-29T00:00:00Z" }
sources:
  - { id: pdf, resource: "TTAK.KO-11.0309_R1.pdf — 원본 PDF (저장소 미포함)", title: "TTAK.KO-11.0309/R1 원본 PDF", author: "TTA", last_modified: "2024-12-06" }
---

> **표준번호**: TTAK.KO-11.0309/R1 | **표준명(국문)**: 오픈소스 소프트웨어 공급망 관리를 위한 소프트웨어 구성요소 목록(SBOM) 속성 규격 | **표준명(영문)**: SBOM(Software Bill of Materials) Attribute Specification for Open Source Software Supply Chain Management | **제정/개정일**: 제정 2022.12.07.(TTAK.KO-11.0309) / 개정 2024.12.06.(TTAK.KO-11.0309/R1)
> 원본: TTAK.KO-11.0309_R1.pdf — 본 문서는 PDF 원문을 마크다운으로 변환한 참고자료입니다.

# 오픈소스 소프트웨어 공급망 관리를 위한 소프트웨어 구성요소 목록(SBOM) 속성 규격

**(SBOM(Software Bill of Materials) Attribute Specification for Open Source Software Supply Chain Management)**

## 표지

- 정보통신단체표준(국문표준)
- 표준번호: TTAK.KO-11.0309/R1
- 개정일: 2024.12.06.
- 표준명(국문): 오픈소스 소프트웨어 공급망 관리를 위한 소프트웨어 구성요소 목록(SBOM) 속성 규격
- 표준명(영문): SBOM(Software Bill of Materials) Attribute Specification for Open Source Software Supply Chain Management
- 발행: TTA 한국정보통신기술협회(Telecommunications Technology Association)

## 표준 작성 관련 정보

- **표준초안 검토 위원회**: 오픈소스 소프트웨어 프로젝트그룹(PG602)
- **표준안 심의 위원회**: 소프트웨어/콘텐츠 기술위원회(TC6)

| 구분 | 성명 | 소속 | 직위 | 위원회 및 직위 |
|---|---|---|---|---|
| 표준(과제) 제안 | 김병선 | 오에스비씨(주)<br>PG602 | 부사장 | PG602 의장 |
| 표준 초안 에디터 | 김병선 | 오에스비씨(주) | 부사장 | PG602 의장 |
| | 류원옥 | ETRI | 책임 | PG602 부의장 |
| | 백영석 | 오에스비씨(주) | 차장 | PG602 간사 |
| | 박수명 | ETRI | 책임 | PG602 위원 |
| | 김정석 | SK텔레콤(주) | 매니저 | PG602 위원 |
| | 장학성 | SK텔레콤(주) | 매니저 | PG602 위원 |
| | 송상효 | 숭실대학교 | 교수 | PG602 특별 위원 |
| | 김종배 | 숭실대학교 | 교수 | PG602 특별 위원 |
| 사무국 담당 | 전세환 | TTA | 선임 | - |

본 문서에 대한 저작권은 TTA에 있으며, TTA와 사전 협의 없이 이 문서의 전체 또는 일부를 상업적 목적으로 복제 또는 배포해서는 안 됩니다.

본 표준 발간 이전에 접수된 지식재산권 확약서 정보는 본 표준의 '부록(지식재산권 확약서 정보)'에 명시하고 있으며, 이후 접수된 지식재산권 확약서는 TTA 웹사이트에서 확인할 수 있습니다. 준용표준인 경우 해당 표준화기구 또는 단체의 웹사이트에서 이를 확인해야 합니다.

본 표준과 관련하여 접수된 확약서 외의 지식재산권이 존재할 수 있습니다.

- **발행인**: 한국정보통신기술협회 회장
- **발행처**: 한국정보통신기술협회 — 13591, 경기도 성남시 분당구 분당로 47 / Tel: 031-724-0114, Fax: 031-724-0109
- **발행일**: 2024. 12. 06.

## 서문

### 1 표준의 목적

이 표준의 목적은 오픈소스 소프트웨어를 활용한 소프트웨어 개발 및 공급에 있어 소프트웨어 사용으로 인한 제반 위험을 예방하기 위해 관리되어야 할 소프트웨어 구성요소 목록(SBOM, Software Bill of Materials)에 대한 표준 속성 규격과 함께 관리 방안을 제정함에 있다.

### 2 주요 내용 요약

최근 오픈소스 소프트웨어 개발 및 사용이 산업 전반에 걸쳐 급증하고 있는 반면 오픈소스 소프트웨어가 사용된 소프트웨어에 대한 명확한 구성요소 목록에 대한 가시화 부족으로 인해 보안취약점 및 라이선스 위반과 같은 위험을 내포하고 있다. 기존에 SPDX, SWID, CyclonDX 등과 같이 소프트웨어 구성요소 목록을 관리하는 포맷이 있지만 위험 예방을 위한 종합적인 구성요소 목록을 제시하지 않고 있고 다양한 공급망의 이해관계자들의 요구사항에 따라 관리해야 할 소프트웨어 구성요소 목록 또한 다양해 질 수 있기 때문에 소프트웨어 공급자들이 적절한 소프트웨어 구성요소 목록 관리에 어려움을 겪고 있다. 본 표준에서는 이러한 다양한 소프트웨어 공급망과 사용목적에 따른 가변적인 소프트웨어 구성요소목록 관리에 있어 소프트웨어 공급자들이 기본적인 기준을 가지고 소프트웨어 구성요소목록을 생성 및 관리할 수 있도록 소프트웨어 개발 및 공급에 공통적으로 필요시 되는 15가지의 소프트웨어 구성요소 관리 항목을 제시한다. 소프트웨어 공급자들은 본 표준에서 제시하고 있는 관리 항목을 기준으로 다양한 이해관계자들의 요구사항에 따라 추가적인 항목을 도출하여 관리할 수 있다.

### 3 인용 표준과의 비교

해당 사항 없음

## Preface

### 1 Purpose

The purpose of this standard is to establish a management plan with the standard attribute specification for the list of software components (Software Bill of Materials) to be managed in order to prevent all risks due to the use of software in software development and supply using open software.

### 2 Summary

While the development and use of open software has been rapidly increasing across industries in recent years, the lack of visibility into a clear list of components for the software in which open software is used poses risks such as security vulnerabilities and license violations. There are existing formats for managing the list of software components such as SPDX, SWID, CyclonDX, etc., but it does not provide a comprehensive list of components for risk prevention. The list of elements can also vary, making it difficult for software providers to manage an appropriate list of software components. In this standard, in the management of the variable software component list according to the various software supply chains and purpose of use, 15 types commonly required for software development and supply so that software providers can create and manage the list of software components with basic standards of software component management items. Software providers can derive and manage additional attributions according to the requirements of various stakeholders based on the management attributions presented in this standard.

### 3 Relationship to Reference Standards

None

## 목차

1. 적용 범위
2. 인용 표준
3. 용어 정의
4. 약어
5. SBOM 속성 규격
   - 5.1 SBOM 표준 속성 규격의 특성
   - 5.2 SBOM 표준 속성 규격
6. 소프트웨어 구성요소 목록 관리 범위
   - 6.1 SBOM Validation Tool
   - 6.2 공급자(Supplier Name) 확인
   - 6.3 저작권자(Author Name) 확인
   - 6.4 컴포넌트 이름(Component Name) 확인
   - 6.5 컴포넌트 버전(Component Version) 확인
   - 6.6 고유 식별자(Unique Identifier) 확인
   - 6.7 컴포넌트 해시(Component Hash) 확인
   - 6.8 라이선스 명(License Name) 확인
   - 6.9 라이선스 결합형태(License Usage) 확인
   - 6.10 보안취약점 DB(Vulnerability DB)
   - 6.11 컴포넌트 간의 관계성(Relationship)
   - 6.12 릴리즈 날짜(Release Date)
   - 6.13 CVE ID(Common Vulnerabilities and Exposures ID)
   - 6.14 CVSS Base Score(Common Vulnerabilities Scoring System Base Score)
   - 6.15 CVSS Severity(CVSS Severity)
7. 소프트웨어 구성요소 목록 관리
   - 7.1 소프트웨어 구성요소 사용 정책 수립
   - 7.2 소프트웨어 구성요소 관리절차 수립
   - 7.3 소프트웨어 구성요소 관리 시스템 구축
   - 7.4 소프트웨어 구성요소 목록 관리 및 업데이트

부록
- Ⅰ-1 지식재산권 확약서 정보
- Ⅰ-2 시험인증 관련 사항
- Ⅰ-3 본 표준의 연계(family) 표준
- Ⅰ-4 참고 문헌
- Ⅰ-5 영문표준 해설서
- Ⅰ-6 표준의 이력

## 1 적용 범위

본 표준은 전 산업의 제품 및 서비스에 관계 없이 내부에서 자체 개발하거나 일부 오픈소스 소프트웨어를 사용한 소프트웨어를 외부에 공급 혹은 제공하는 공급망에 포함된 모든 조직 및 기업들을 대상으로 소프트웨어의 사용으로 인한 보안 취약점, 저작권 위반과 같은 위험을 예방하기 위해 소프트웨어를 구성하는 구성요소 목록에 포함할 수 있는 표준 속성 규격과 관리 절차를 제시한다.

## 2 인용 표준

해당 사항 없음.

## 3 용어 정의

### 3.1 오픈소스 소프트웨어(公開-, open software)

누구나 자유롭게 사용하고 수정하거나 재배포할 수 있도록 공개하는 소프트웨어. 누구에게나 이용과 복제, 배포가 자유롭고, 특히 소스 코드에 대한 접근을 통하여 개작과 재배포가 자유롭다는 뜻이나 무료와 혼동할 수 있어 'free' 대신에 'open'을 공식적으로 사용한다. 오픈소스 소프트웨어라도 오픈소스 소프트웨어 본래 의미를 유지하기 위해 다양한 라이선스 정책을 만들어 이를 지키도록 요구하고 있다. 따라서 상업적인 목적으로 오픈소스 소프트웨어를 사용하려고 할 때에는 사전에 라이선스의 각 조항들을 검토할 필요가 있다. 공개 소스 소프트웨어와 같은 의미로 사용된다.

[출처] TTAK.KO-12.0002/R3 정보 보호 기술 용어

### 3.2 공급망 관리(supply chain management)

소프트웨어가 배포되는 시점에서 포함될 수 있는 외부의 소프트웨어에 대한 위험 요소를 관리하는 프로세스

[출처] TTAK.KO-11.0257 개방형 연구개발을 위한 오픈소스 소프트웨어 커뮤니티 거버넌스 지침

### 3.3 SBOM(Software Bill of Materials)

소프트웨어 구성요소 목록, 소프트웨어에 포함된 컴포넌트 명, 버전, 라이선스, 체크섬 정보와 같은 소프트웨어를 구성하고 있는 다양한 메타데이타의 목록이다.

### 3.4 SPDX(Software Package Data Exchange)

소프트웨어 교환을 위한 패키지 데이터. 리눅스 파운데이션 SPDX 워킹그룹에 의해 제정되어 활용되고 있다. 현재 구성 요소, 라이선스, 저작권 및 보안 참조를 포함하여 소프트웨어 BOM 정보를 전달하기 위한 공개 표준이다. SPDX는 회사와 커뮤니티가 중요한 데이터를 공유할 수 있는 공통 형식을 제공하여 중복 작업을 줄임으로써 규정 준수를 간소화하고 개선하는데 기여하고 있다

[출처 : https://spdx.dev/]

### 3.5 SWID(Software Identification Tags)

ISO/IEC 19770-2:2015 소프트웨어 제품을 설명하기 위한 구조화 된 메타데이터 형식을 정의하는 소프트웨어 식별 (SWID) 태그 표준으로서 SWID 태그 문서는 소프트웨어 제품을 식별하고 제품 버전을 특성화하는 구조화 된 데이터 요소 집합이며 제품의 생산 및 배포에서 역할을 맡은 조직 및 개인, 소프트웨어 제품을 구성하는 아티팩트에 대한 정보, 소프트웨어 제품 간의 관계 및 기타 설명 메타 데이터, 소프트웨어의 배포 수명주기 동안 소프트웨어 설치 관리 자동화 정보, 소프트웨어 자산 관리 및 보안 도구를 제공한다. SWID 태그는 소프트웨어 자산 관리 (SAM) 프로세스의 일부로 소프트웨어 인벤토리 자동화, 컴퓨팅 장치에 존재하는 소프트웨어 취약성 평가, 누락 된 패치 감지, 구성 체크리스트 평가 대상 지정, 소프트웨어 무결성 검사, 설치 및 실행 화이트리스트 / 블랙리스트를 지원한다.

[출처] https://csrc.nist.gov/projects/Software-Identification-SWID/

### 3.6 CyclonDX

2017년 소프트웨어 보안 개선을 위한 비영리재단인 The Open Web Application Security Project® (OWASP)의 오픈 소스 공급망 구성 요소 분석 플랫폼인 OWASP Dependency-Track 과 함께 사용하도록 설계 되었으며 오픈소스 취약성 식별, 라이선스 규정 준수 및 낙후된 컴포넌트 분석 목적으로 사용된다. 현재 금융 서비스, 제조, 정부, 소프트웨어 및 보안 회사에 이르는 수천 개의 조직이 CycloneDX SBOM을 활용하고 있다

[출처] : https://cyclonedx.org/

### 3.7 CWE(Common Weakness Enumeration)

소프트웨어 취약점을 사전식으로 분류해 쉽게 찾아 볼 수 있도록 정보를 제공한다. CWE는 미국국토안보부(The U.S. Department of Homeland Security)에서 관리하고 있으며, 소프트웨어의 취약성을 프로그래머가 쉽게 접근할 수 있도록 구성한다. 수집된 취약점 항목을 뷰, 카테고리, 취약점, 복합요소를 기준으로 분류하여 살펴볼 수 있는 특징을 가지고 있으며, 취약점 항목에 대한 갱신은 현재에도 지속적으로 이루어 지고 있다. 취약점이 발견될 때마다 CWE-[번호] 형태로 등록되며, 3가지인 Research Concepts/ Development Concepts/ Architectural Concepts 분류해 놓았다.

[출처] https://cwe.mitre.org

### 3.8 CWSS(Common Weakness Scoring System)

CWSS는 소프트웨어 보안 약점의 중요도를 평가하는 평가체계로 CWE 프로젝트의 일부로 수행되고 있다. CWE와 CWSS의 특징은 안전한 소프트웨어의 개발과 보안 유지에 책임이 있는 당사자들인 정부, 학계, 산업체들이 모여서 만드는 커뮤니티 형태의 협업이라는 점에 있다. 현재 이 프로젝트는 미국 NCSD(National Cyber Security Division)와 미국 DHS (Department of Homeland Security)의 지원을 받아서 진행되고 있다. CWSS는 소프트웨어에 일반적으로 발생하는 다양한 약점에 대하여 제거의 우선순위를 줄 수 있는 정량적인 기준을 제시한다. 정량적인 기준을 제시하기 위한 다양한 메트릭을 약점 자체의 심각성(Base Finding Metric Group), 공격 측면의 심각성(Attack Surface Matric Group), 환경적 측면의 심각성(Environment Matric Group)으로 분류하여 그 정량적 기준과 함께 제시하고 있으며, 아울러 소프트웨어가 사용되는 도메인의 특성을 고려하여 중요성을 조정할 수 있는 방법론인 CWRAF(Common Weakness Risk Analysis Framework)를 제시하고 있다. CWE 사이트에는 CWSS도 있는데, CWE에 등록된 취약점의 위험성을 정량화하기 위해 점수를 매겨 놓았다. CWSS는 CVSS와 유사하면서 일반적인 취약점에 대한 점수체계를 만들기 위해 CERT를 주축으로 진행중인 평가체계이다. 즉, CWSS가 CVSS보다 광범위하다고 볼 수 있다.

[출처] https://cwe.mitre.org/cwss/cwss_v1.0.1.html

### 3.9 SANS Top 25(SysAdmin, Audit, Network, Security)

SANS(SysAdmin, Audit, Network, Security)는 산학협동 연구소인데, CWE에 리스팅된 소프트웨어 취약점 중 가장 위험한 25개의 취약점에 점수를 매긴 리스트를 제공한다. 순위를 정하기 위해 CWSS를 사용했으며, 취약점을 완화할 방법을 제공한다. 즉, 소프트웨어의 심각한 취약점으로 이어질 수 있는 가장 광범위하고 치명적인 오류 목록이다. 개발자는 소프트웨어를 출하하기 전에 발생하는 모든 공통적인 실수를 확인하고 예방함으로서 오픈소스 소프트웨어 업계를 괴롭히는 종류의 취약점을 예방할 수 있도록 돕는 도구이다.

[출처] https://www.sans.org

### 3.10 CVE(Common Vulnerabilities and Exposures)

CVE는 시간대 별로 발생된 보안취약점 또는 위험 노출을 정리한 목록을 제공한다. MITRE를 주축으로 각종 소프트웨어 회사나 CERT 같은 기관에서 감지되는 보안취약점을 보고하면 CVE 조정위원회에서 목록을 관리한다. CWE가 일반적인 취약점의 분류체계라면, CVE는 발견된 보안 취약점의 히스토리다. CVE의 형식은 CVE-[해당년도]-[일련번호]로 표현되며, 시간에 따라 감지된 보안 취약점 또는 위험 노출을 정리해 둔 목록이라 할 수 있다.

[출처] https://cve.mitre.org

### 3.11 NVD(National Vulnerability Database)

보안 콘텐츠 자동화 프로토콜(SCAP)을 사용하여 표현된 미국 정부의 표준 기반 취약점 관리 데이터 저장소이다. 이 데이터는 취약점 관리, 보안 측정 및 규정 준수의 자동화를 가능하게 한다. NVD는 보안 체크리스트, 소프트웨어의 결함, 잘못된 구성, 제품 이름, 평가 메트릭과 관련된 보안 데이터베이스를 포함하고 있다. NVD의 취약점 심각도 수준 평가에 관한 기준으로 CVE 항목에 대해 CVSS 벡터 값에 근거하여 산출된 점수에 근거하여 심각성 정도를 정의한다. NVD는 CVSS 계산 결과에 근거하여 각 취약점에 대해 취약점 심각도 수준을 공개하고 있으며 년도 별로 전체 취약점을 CVSS 기본 점수에 따라 심각도를 High/ Medium/ Low로 분류한다.

[출처] https://nvd.nist.gov/

### 3.12 CVSS(Common Vulnerabilities Scoring System)

CVSS는 평가된 취약점의 우선순위를 부여하여 관리하기 위해, IT 취약점에 대한 영향과 특성을 표현하기 위한 공통 프레임워크를 제공한다. 만일 취약점이 임의로 배점된다면 사용자들은 이에 대해 혼란을 느낄 수 있다. 이에 점수가 어떻게 부여되었는지, 지난 번 릴리즈 된 것과 지금 것과는 어떻게 다른지 등에 관한 질문이 가능할 것이다. CVSS를 통해 모든 사람들은 점수에 관련된 개별 특성들을 접근할 수 있다. 또한, 환경 요소가 점수화되어 어떤 조직의 특정한 위험을 대표하는 점수로써 다른 취약점에 비해 어느 정도 중요한지 인식이 가능하게 한다. NIST와 카네기멜론 대학의 연구를 바탕으로 개발되어 현재 FIRST (Forum of Incident Response and Security Teams)에 의하여 관리되고 있는 취약점 평가 표준이다. 공식적인 최신 버전은 2005 년에 발표된 2.0 표준이며, 2014년의 버전 3.0이 발표되었다. CVSS 버전 2 평가항목은 기본(base), 시간(temporal), 환경(environmental)과 같은 3가지 메트릭 그룹으로 구성된다.

[출처] https://www.cvedetails.com

## 4 약어

| 약어 | 원어 |
|---|---|
| SBOM | Software Bill of Materials |
| SPDX | Software Package Data Exchange |
| SWID | Software Identification Tags |
| CWE | Common Weakness Enumeration |
| CWSS | Common Weakness Scoring System |
| CVE | Common Vulnerabilities and Exposures |
| NVD | National Vulnerability Database |
| CVSS | Common Vulnerabilities Scoring System |

## 5 SBOM 속성 규격

### 5.1 SBOM 표준 속성 규격의 특성

기존의 SBOM의 유형인 SPDX, SWID, CyclonDX 등에서 다루고 있는 구성요소는 SPDX의 경우 오픈소스 소프트웨어 라이선스, SWID와 CyclonDX는 보안 취약점을 중심으로 하고 있어 SBOM의 주요 목적인 보안취약점과 라이선스 위반 위험 예방을 종합적으로 관리함에 있어 어려움이 있다. 따라서, 본 표준에서는 보안취약점과 라이선스 위반 위험 예방을 중심으로 SBOM에 포함할 수 있는 15가지 표준 속성 규격을 제시하였다.

### 5.2 SBOM 표준 속성 규격

SBOM 속성은 소프트웨어 공급망을 구성하는 이해관계자들의 요구사항에 따라 달라질 수 있지만 본 표준에서는 소프트웨어를 개발, 배포, 유지보수 함에 있어서 기본적으로 필요시 되는 필수적인 관리 구성요소로서 다음과 같은 표준 속성 규격을 제시한다.

**<표 5-1> SBOM 표준 속성 규격**

| 구분(Baseline) | 속성 (Attribution) |
|---|---|
| ① SBOM 검증 도구 (SBOM Validation Tool Name) | ex) Folosology |
| ② 공급자 (Supplier Name) | ComponentSupplier: |
| ③ 저작권자 (Author Name) | Component Author: |
| ④ 컴포넌트 (Component Name) | ComponentName: |
| ⑤ 버전 (Version String) | ComponentVersion: |
| ⑥ 고유식별자(Unique Identifier) | FormatID: |
| ⑦ 컴포넌트 해시 (Component Hash) | FileChecksum: |
| ⑧ 라이선스 명 (License Name) | Component License: |
| ⑨ 라이선스 결합형태(License Usage) | Dynamic/Satic Linking: |
| ⑩ 보안취약점 DB(Vulnerability DB) | VulnerabilityDB : NVD |
| ⑪ 관계성 (Relationship) | IncludeComponent, ImportComponent |
| ⑫ 릴리즈 날짜(Release Date) | ReleaseDate: |
| ⑬ CVE ID | CVE-Year-Serial Number |
| ⑭ CVSS Base Score | Base : , Impact : , Exploitability : |
| ⑮ CVSS Severity | CVSS Severity: High, Medium, Low, None |

## 6 소프트웨어 구성요소 목록 관리 범위

### 6.1 SBOM 검증(SBOM Validation Tool)

소프트웨어 구성요소를 정확히 파악하기 위해서는 소스코드 및 종속성 분석을 통해 사용된 외부 컴포넌트와 버전 라이선스 및 보안취약점을 식별할 수 있는 스캐닝 도구를 사용하여야 한다. 개발자에 의존하여 소프트웨어 개발에 사용된 외부 컴포넌트와 관련 정보를 파악할 수도 있겠지만 외부 컴포넌트들은 동일한 소스코드 라도 다양한 출처와 정보를 가지고 있기 때문에 신뢰성 있는 원 출처와 정보를 파악하기 어렵고 버전에 따른 보안취약점과 패치버전을 파악함에 있어 어려움이 있다. 따라서, SBOM을 작성함에 있어서는 공신력 있는 소스코드 분석 스캐닝 도구를 사용하여야 한다.

### 6.2 공급자(Supplier Name) 확인

소프트웨어를 통한 위험관리와 책임을 위해 공급자 이름에 대한 확인이 필요하다.

### 6.3 저작권자(Author Name) 확인

소프트웨어의 라이선스에 따른 사용권한, 기술적 협의 등을 위해 해당 소프트웨어의 원 저작권자에 대한 확인이 필요하다.

### 6.4 컴포넌트 이름(Component Name) 확인

오픈소스 소프트웨어 커뮤니티에는 많은 개발자들이 참여하고 있고 코드가 공개된 만큼 보안취약점에 대한 발견과 문제점 해결을 통한 보안 패치 등의 해결책이 빠르게 제공되고 있다. 또한 오픈소스 소프트웨어에는 다양한 라이선스가 적용되어 있어 사용 결합형태와 조건에 따라 라이선스 위반이 발생되지 않도록 관리하여야 한다. 이러한 보안취약점과 라이선스를 관리하기 위해서는 사용된 정확한 컴포넌트 이름을 식별하여야 한다. 동일한 소스코드에도 다양한 컴포넌트가 교집합으로 적용될 수도 있고 잘못된 컴포넌트 이름이 적용되어 있을 수도 있기 때문에 명확한 컴포넌트 이름을 식별하기 위해서는 전문적인 스캐닝 도구를 통한 확인이 필요하다.

### 6.5 컴포넌트 버전(Component Version) 확인

오픈소스 소프트웨어 커뮤니티에는 많은 개발자들이 참여하고 있고 코드가 공개된 만큼 보안취약점에 대한 발견과 문제점 해결이 빠르지만 커뮤니티 참여 개발자가 많지 않거나, 기술 지원 전문 업체가 존재하지 않을 경우에는 관리 소홀로 인해 보안성이 더 취약할 수밖에 없다. 따라서, 소프트웨어 개발에 사용된 명확한 컴포넌트 이름과 함께 버전에 대한 확인이 필요하다. 버전 확인 및 관리에 있어서는 다음과 같은 경우에 대한 검토가 필요하다. 보안 패치가 빨리 이루어졌다 하더라도 이용자 측에서 체계적인 컴포넌트 식별과 버전 관리가 이루어지지 않은 경우, 버전 변경에 따른 호환성 문제 등을 우려하여 이용자가 패치를 적용하지 않는 경우, 소프트웨어 개발 시 오픈소스 소프트웨어 사용 여부가 확인되지 않는 경우, 소스코드 확보가 어려운 외주 개발 모듈 등으로 인해 오픈소스 소프트웨어가 사용 되었는지 여부조차 확인하기 어려운 경우이다. 이러한 경우에는 버전확인을 통한 보안 패치가 적용되기 어렵기 때문에 이를 고려한 오픈소스 소프트웨어 관리 및 외주개발 모듈에 대한 별도 관리가 필요하다.

### 6.6 고유 식별자(Unique Identifier) 확인

소프트웨어 컴포넌트 단위별 SBOM에서 사용하는 고유 식별자를 할당하여 관리하여야 한다.

### 6.7 컴포넌트 해시(Component Hash) 확인

해당 소프트웨어를 구성하고 있는 개별 파일들에 대한 고유한 정보 확인을 통해 신뢰성을 확보하여야 한다.

### 6.8 라이선스 명(License Name) 확인

오픈소스 소프트웨어에 적용된 라이선스 위반으로 인한 제반 위험 요소를 예방하기 위해서는 오픈소스 소프트웨어에 대한 라이선스를 명확히 확인하여야 한다. 라이선스 확인을 통해 소프트웨어의 사용 목적에 부합된 오픈소스 소프트웨어 사용 여부 검토는 물론, 사용된 오픈소스 소프트웨어 간의 라이선스 호환성에 대한 검토 또한 필요하다.

### 6.9 라이선스 결합형태(License Usage) 확인

오픈소스 소프트웨어 컴포넌트의 사용 결합형태는 오픈소스 소프트웨어에 적용된 라이선스 적용범위에 있어 매우 중요하다. 따라서, 해당 컴포넌트를 수정하여 사용하는지, 수정하지 않고 파일단위로 복제하여 사용하는지, 라이브러리를 동적 혹은 정적 링킹을 통해 사용하는지 등에 대한 명확한 결합형태에 대한 확인이 필요하다.

### 6.10 보안취약점 DB(Vulnerability DB)

최근 오픈소스 소프트웨어에서 심각한 취약점이 발견되고 있으며 이로 인한 해킹사고 또한 계속해서 발생하고 있다. 2021년 아파치 소프트웨어 재단의 Java 프로그래밍 언어로 제작된 Log4j 라이브러리를 사용하는 대부분의 인터넷 서비스에서 매우 중대한 보안 취약점이 발견된 사건이 있었다. 테나블(Tenable)에서는 이 사태를 '하트블리드와 CPU 게이트 따위는 비교도 안 될 만큼, 컴퓨터 인터넷 역사를 통틀어 사상 최악의 보안 결함일 수도 있다'고 경고했다. 또한, 2022년 4월 해커들이 최근 발견된 스프링 프레임워크 내 원격코드실행(RCE) 취약점인 '스프링4셸'을 악용해, 봇넷 악성코드를 배포하고 감염시킨 것으로 확인됐다. 글로벌 사이버보안업체 트렌드마이크로는 스프링4셸(CVE-2022-22965) 취약점 악용 분석 보고서를 공개했다. 스프링은 자바 기반 애플리케이션 개발을 빠르고 효율적으로 진행할 수 있게 지원하는 오픈소스 프레임워크이다. 이처럼 오픈소스 소프트웨어에서 많은 취약점이 존재하는 가장 큰 이유는 소스코드가 공개되어 있다는 점이다. 소스코드가 공개된 만큼 공격자 입장에서도 공격 대상 선정 및 악의적인 역분석이 매우 용이할 수 있다. 따라서, 미국의 NIST(National Institute of Standards and Technology/ U.S. Department of Commerce)에서는 이러한 오픈소스 소프트웨어의 보안취약점에 대한 관리를 위해 NVD(National Vulnerability Database)를 통해 신규 보안취약점 및 취약 심각도를 평가하여 공개하고 있다. SBOM 관리의 핵심 목적은 보안취약점에 대한 예방이기 때문에 해당 보안취약점에 대한 출처 확인은 매우 중요하다.

### 6.11 컴포넌트 간의 관계성(Relationship)

소프트웨어 컴포넌트 간의 종속성 및 의존성을 확인하여 라이브러리와 같은 보안취약점 패치 여부 및 라이선스 적용 범위를 확인하여야 한다.

### 6.12 릴리즈 날짜(Release Date)

소프트웨어 컴포넌트의 라이선스 출처와 보안취약점 버전의 상호 확인을 위해 해당 컴포넌트의 릴리즈 날짜에 대한 확인이 필요하다.

### 6.13 CVE ID(Common Vulnerabilities and Exposures ID)

CVE ID는 공개적으로 알려진 보안 결함 목록으로서 다른 버그로부터 독립적으로 수정할 수 있는 결함이다. 시간대 별로 발생된 보안취약점 또는 위험 노출을 정리한 목록을 제공한다. 소프트웨어의 보안취약점에 활용되는 위험관리 프레임워크는 소프트웨어의 보안 약점의 중요도를 평가하는 평가체계로 CWE 프로젝트의 일부로 수행되고 있는 CWSS (Common Weakness Scoring System), 산학협동 연구소인 SANS(SysAdmin, Audit, Network, Security)에서 관리하는 CWE에 리스팅된 소프트웨어 취약점 중 가장 위험한 25개의 취약점에 점수를 매긴 리스트를 제공하는 SANS Top 25, 시간대 별로 발생된 보안취약점 또는 위험 노출을 정리한 목록인 CVE (Common Vulnerabilities and Exposures), 평가된 취약점의 우선순위를 부여하여 관리하기 위해 IT 취약점에 대한 영향과 특성을 표현하기 위한 공통 프레임워크를 제공하는 CVSS (Common Vulnerabilities Scoring System)와 보안 콘텐츠 자동화 프로토콜(SCAP)을 사용하여 표현된 미국 정부의 표준 기반 취약점 관리 데이터 저장소인 NVD가 활용되고 있다. 본 표준에서는 다양한 위험관리 프레임워크 중에서 가장 직관적이면서도 일반적으로 활용되고 있는 CVE ID와 CVSS Base Score, CVSS Severity를 위험관리 구성요소로 제시한다.

### 6.14 CVSS Base Score(Common Vulnerabilities Scoring System Base Score)

소프트웨어 컴포넌트의 보안취약점에 대한 기본 위험성, 영향성, 악용 가능성에 대한 0 - 10점 범위의 점수로서 취약점에 대한 지표를 제공한다.

### 6.15 CVSS Severity(CVSS Severity)

소프트웨어 컴포넌트의 보안취약점에 대한 심각성 지표로서 심각도에 따라 High, Medium, Low, None으로 구분하여 심각성에 대한 정도를 제공한다.

## 7 소프트웨어 구성요소 목록 관리

### 7.1 소프트웨어 구성요소 사용 정책 수립

소프트웨어 구성요소를 소프트웨어 개발과 공급 목적에 부합되게 효율적으로 관리하기 위해서는 소프트웨어 개발에 활용되는 외부 컴포넌트들에 대한 사용정책이 명확해야 한다. 예를 들어 소스코드가 공개되어서는 안되는 소프트웨어 개발의 경우 소스코드 공개가 의무적으로 발생되는 GPL계열의 오픈소스 소프트웨어는 사용을 금지하는 정책이 필요하게 된다. 또한 보안취약점 관리에 있어서도 자산 중요도에 따라 NVD에서 분류하고 있는 하이 리스크에 해당되는 경우 사용을 금지할 수 있다.

### 7.2 소프트웨어 구성요소 관리절차 수립

소프트웨어 개발 및 공급 목적에 부합한 소프트웨어 구성요소에 대한 사용정책이 수립되었으면 정책준수를 위해 필요시 되는 관리절차를 수립하고 적절한 권한과 책임을 부여하여야 한다.

**<표 7-1> 소프트웨어 구성요소 관리절차 수립**

| 단계 | 업무 |
|---|---|
| 요구사항 정의 | 소프트웨어 개발 및 배포 공급망을 구성하는 이해관계자들에 대한 구성요소 요구사항 정의<br>EX) 오픈소스 소프트웨어 사용여부, 오픈소스 소프트웨어 라이선스 사용 범위, 보안취약점 위험수준, 검증 도구를 통한 SBOM 생성 여부 등 |
| 계획수립 | 소프트웨어 개발 및 배포 공급망 이해관계자들의 요구사항에 따른 SBOM 생성 및 관리 계획 수립<br>EX) 오픈소스 소프트웨어 사용여부에 따른 컴포넌트 결합방식, 검증 주기 등 |
| 개발 | 소프트웨어 구성요소 목록 관리 계획에 따른 개발 및 검증 |
| 테스트 | 요구사항 & 개발 적합성 여부 검토 |
| 배포 | SBOM 구성에 따른 의무사항 준수<br>EX) 오픈소스 소프트웨어 사용에 따른 고지 및 소스코드 공개 등 |
| 운영 및 유지관리 | 요구사항 준수를 위한 보안취약점 모니터링 및 패치를 통한 위험 수준 관리 |

### 7.3 소프트웨어 구성요소 관리 시스템 구축

소프트웨어 개발 및 공급 목적에 부합한 소프트웨어 구성요소를 적절히 관리하기 위해서는 요구사항에 따른 관리 계획수립을 기반으로 소프트웨어 구성요소들이 적절히 도출될 수 있도록 개발된 코드를 분석하여 구성요소를 파악하는 도구 및 관리 시스템 구축이 필요하다. 소스코드 분석을 통해 소프트웨어 구성요소 목록을 생성하는 도구를 구축함에 있어서는 도구에 따라 구성요소 생성 기준 및 생성 항목이 상이하기 때문에 소프트웨어 개발 및 배포 공급망을 구성하는 이해관계자들과의 사전 협의를 통해 필요 구성요소 목록을 생성할 수 있는 도구를 신중히 선택 활용하여야 한다.

### 7.4 소프트웨어 구성요소 목록 관리 및 업데이트

소프트웨어 구성요소 목록은 공급망을 구성하는 이해관계자들의 요구사항과 소프트웨어의 사용 목적에 따라 다양하고 변경될 수 있기 때문에 정형화된 소프트웨어 구성요소 목록 포맷을 관리하기 보다는 요구사항에 따라 적절히 구성요소 목록을 생성하고 업데이트할 수 있도록 유연한 관리 정책과 절차에 따른 목록관리 및 업데이트가 필요하다.

## 부록 Ⅰ-1 지식재산권 확약서 정보

(본 부록은 표준을 보충하기 위한 내용으로 표준의 일부는 아님)

아래에 기재된 지식재산권 확약서 이외에도 본 표준이 발간된 후 접수된 확약서가 있을 수 있으니, TTA 웹사이트에서 확인하시기 바랍니다.

해당 사항 없음

## 부록 Ⅰ-2 시험인증 관련 사항

(본 부록은 표준을 보충하기 위한 내용으로 표준의 일부는 아님)

해당 사항 없음

## 부록 Ⅰ-3 본 표준의 연계(family) 표준

(본 부록은 표준을 보충하기 위한 내용으로 표준의 일부는 아님)

해당 사항 없음

## 부록 Ⅰ-4 참고 문헌

(본 부록은 표준을 보충하기 위한 내용으로 표준의 일부는 아님)

아래 기재된 참고 문헌의 발간일이 기재된 경우, 해당 표준(문서)의 해당 버전에 대해서만 유효하며, 연도를 표시하지 않은 경우에는 해당 표준(권고)의 최신 버전을 따른다.

- [1] https://csrc.nist.gov/projects/Software-Identification-SWID/
- [2] https://spdx.dev/
- [3] https://cyclonedx.org/
- [4] https://cwe.mitre.org
- [5] https://cwe.mitre.org/cwss/cwss_v1.0.1.html
- [6] https://www.sans.org
- [7] https://cve.mitre.org
- [8] https://nvd.nist.gov/
- [9] https://www.cvedetails.com

## 부록 Ⅰ-5 영문표준 해설서

(본 부록은 표준을 보충하기 위한 내용으로 표준의 일부는 아님)

해당 사항 없음

## 부록 Ⅰ-6 표준의 이력

(본 부록은 표준을 보충하기 위한 내용으로 표준의 일부는 아님)

| 판수 | 채택일 | 표준번호 | 내용 | 담당 위원회 |
|---|---|---|---|---|
| 제1판 | 2022.12.07 | 제정<br>TTAK.KO-11.0309 | - | 공개 소프트웨어 프로젝트 그룹(PG 602) |
| 제2판 | 2024.12.06 | 개정<br>TTAK.KO-11.0309/R1 | 오픈소스 등 용어 및 내용 현행화 | 오픈소스 소프트웨어 프로젝트 그룹(PG 602) |
