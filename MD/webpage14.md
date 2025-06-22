[跳到主要內容](#main)
跳過到　Ask Learn　聊天體驗

已不再支援此瀏覽器。

請升級至 Microsoft Edge，以利用最新功能、安全性更新和技術支援。

[下載 Microsoft Edge](https://go.microsoft.com/fwlink/p/?LinkID=2092881 )
[Internet Explorer 和 Microsoft Edge 的詳細資訊](https://learn.microsoft.com/en-us/lifecycle/faq/internet-explorer-microsoft-edge)

目錄

結束焦點模式

Ask Learn

Ask Learn

目錄
閱讀英文

加

新增至計劃

---

#### 共用方式為

Facebook
x.com
LinkedIn
電子郵件

---

列印

---

注意

需要授權才能存取此頁面。 您可以嘗試登入或變更目錄。

需要授權才能存取此頁面。 您可以嘗試變更目錄。

# 使用 Microsoft Entra ID 設定 FactSet 以進行單一登錄

* 2025-04-30

意見反應

## 本文內容

在本文中，您將瞭解如何整合 FactSet 與 Microsoft Entra ID。 在將 FactSet 與 Microsoft Entra ID 整合時，您可以：

* 在 Microsoft Entra 識別碼中控制可透過同盟存取 FactSet URL 的人員。
* 讓使用者使用其Microsoft Entra 帳戶自動登入 FactSet。
* 在一個中央位置管理您的帳戶。

## 先決條件

本文中所述的案例假設您已經具備下列必要條件：

* 具有有效訂閱的 Microsoft Entra 用戶帳戶。 如果您還沒有帳戶，您可以 [免費建立帳戶](https://azure.microsoft.com/free/?WT.mc_id=A261C142F)。
* 下列其中一個角色：
  + [應用程式管理員](/zh-tw/entra/identity/role-based-access-control/permissions-reference#application-administrator)
  + [雲端應用程式管理員](/zh-tw/entra/identity/role-based-access-control/permissions-reference#cloud-application-administrator)
  + [應用程式擁有者](/zh-tw/entra/fundamentals/users-default-permissions#owned-enterprise-applications)。

* 已啟用 FactSet 單一登入 （SSO） 的訂用帳戶。

## 案例描述

在本文中，您會在測試環境中設定及測試 Microsoft Entra SSO。

* FactSet 支援 **SP** 起始的 SSO。

注意

此應用程式的標識碼是固定字串值，因此一個租使用者中只能設定一個實例。

## 從畫廊新增 FactSet

若要設定將 FactSet 整合到 Microsoft Entra ID 中，您需要從資源庫將 FactSet 新增到受控 SaaS 應用程式清單。

1. 以至少雲端[應用程式管理員](https://entra.microsoft.com)身分登入 [Microsoft Entra 系統管理中心](../role-based-access-control/permissions-reference#cloud-application-administrator)。
2. 流覽至 **Entra ID**>**企業應用程式**>**新增應用程式**。
3. 在 [ **從資源庫新增** ] 區段的搜尋方塊中輸入 **FactSet** 。
4. 從結果面板中選取 **[FactSet** ]，然後新增應用程式。 將應用程式新增至您的租用者時，請稍候幾秒鐘。

或者，您也可以使用 [企業應用程式設定精靈](https://portal.office.com/AdminPortal/home?Q=Docs#/azureadappintegration)。 在此精靈中，您可以將應用程式新增至租戶，將使用者或群組新增至應用程式，指派角色，以及完成 SSO 設定。
[深入瞭解 Microsoft 365 精靈](/zh-tw/microsoft-365/admin/misc/azure-ad-setup-guides)。

## 設定並測試 Microsoft Entra SSO 以用於 FactSet

以名為 **B.Simon** 的測試用戶，設定及測試Microsoft Entra SSO 與 FactSet 搭配運作。 若要讓 SSO 能夠運作，您必須建立 Microsoft Entra 使用者與 FactSet 中相關使用者之間的連結關聯性。

若要設定及測試與 FactSet 搭配運作的 Entra SSO Microsoft，請執行下列步驟：

1. **[設定 Microsoft Entra SSO](#configure-azure-ad-sso)** - 讓使用者能夠使用此功能。
   1. **建立 Microsoft Entra 測試使用者** - 以使用 B.Simon 測試Microsoft Entra 單一登錄。
   2. **指派 Microsoft Entra 測試使用者** - 讓 B.Simon 能夠使用 Microsoft Entra 單一登錄。
2. **[設定 FactSet SSO](#configure-factset-sso)** - 在應用程式端設定單一登入設定。
   1. **[建立 FactSet 測試使用者](#create-factset-test-user)** - 以在 FactSet 中創建一個對應的 B.Simon 並將其連結到 Microsoft Entra 用戶的表示。
3. **[測試 SSO](#test-sso)** - 確認組態是否正常運作。

## 設定 Microsoft Entra SSO

請遵循下列步驟來啟用 Microsoft Entra SSO。

1. 以至少雲端[應用程式管理員](https://entra.microsoft.com)身分登入 [Microsoft Entra 系統管理中心](../role-based-access-control/permissions-reference#cloud-application-administrator)。
2. 流覽至 **Entra ID**>**Enterprise 應用程式**>**FactSet**>**單一登入**。
3. 在 [ **選取單一登錄方法]** 頁面上，選取 **[SAML**]。
4. 在 [ **使用 SAML 設定單一登錄** ] 頁面上，選取 **[基本 SAML 組態** ] 的鉛筆圖示以編輯設定。

   ![顯示如何編輯基本 SAML 設定的螢幕快照。](common/edit-urls.png "基本組態")
5. 在 [基本 SAML 組態] 區段上，執行下列步驟：

   一個。 在 [識別碼] 文字方塊中，輸入 URL：`https://auth.factset.com`

   b。 在 [回覆 URL] 文字方塊中，輸入 URL：`https://auth.factset.com/sp/ACS.saml2`
6. 在 [以 SAML 設定單一登入] 頁面上的 [SAML 簽署憑證] 區段中，尋找 [同盟中繼資料 XML]，然後選取 [下載] 來下載中繼資料檔案，並將其儲存在電腦上。

   ![顯示 [憑證下載] 鏈接的螢幕快照。](common/metadataxml.png "證書")
7. 在 [ **設定 FactSet** ] 區段上，根據您的需求複製適當的 URL。

   ![螢幕快照顯示如何複製適當的設定URL。](common/copy-configuration-urls.png "元數據")

### 建立並指派 Microsoft Entra 測試使用者

遵循 [建立和指派用戶帳戶](../enterprise-apps/add-application-portal-assign-users) 快速入門中的指導方針，以建立名為 B.Simon 的測試用戶帳戶。

## 設定 FactSet SSO

若要在 FactSet 端設定單一登錄（SSO），您必須造訪 FactSet 的[控制中心](https://controlcenter.factset.com)，並在  頁面上，從 Azure 入口網站設定>並配置適當的複製 URL。 如果您需要存取此頁面，請連絡 [FactSet 支援小組](https://www.factset.com/contact-us) ，並要求 FactSet 產品 8514（控制中心 - 來源 IP、安全性 + 驗證）。

### 建立 FactSet 測試使用者

請與您的 FactSet 帳戶支援代表合作，或連絡 [FactSet 支援小組，在 FactSet](https://www.factset.com/contact-us) 平臺中新增使用者。 用戶必須先建立並啟用，才能使用單一登錄。

## 測試 SSO

在本節中，您會使用下列選項來測試您的 Microsoft Entra 單一登錄設定。

* FactSet 僅支援SP起始的SAML。 您可以訪問任何已驗證的 FactSet URL，例如 [問題追蹤器](https://issuetracker.factset.com) 或 [FactSet-Web](https://my.factset.com)，在登入入口網站上選擇 **單一 Sign-On （SSO）**，然後在後續頁面中輸入您的電子郵件地址來測試 SSO。 如需其他資訊和使用方式，請參閱提供的文件。

## 相關內容

設定 FactSet 後，您可以強制執行會話控件，以即時防止組織的敏感數據遭到外泄和滲透。 會話控制延伸自條件存取。
[瞭解如何使用適用於 Cloud Apps 的 Microsoft Defender 強制執行會話控制](/zh-tw/cloud-app-security/proxy-deployment-aad)。

---

## 意見反應

此頁面對您有幫助嗎？

Yes

No

[提供產品意見反應](https://feedback.azure.com/d365community/forum/22920db1-ad25-ec11-b6e6-000d3a4f0789)

---

## 其他資源

### 本文內容

## 其他資源

zh-tw

[您的隱私權選擇](https://aka.ms/yourcaliforniaprivacychoices)

佈景主題

* 淺色
* 深色
* 高對比

* [舊版本](https://learn.microsoft.com/zh-tw/previous-versions/)
* [部落格](https://techcommunity.microsoft.com/t5/microsoft-learn-blog/bg-p/MicrosoftLearnBlog)
* [參與](https://learn.microsoft.com/zh-tw/contribute)
* [隱私權](https://go.microsoft.com/fwlink/?LinkId=521839)
* [使用規定](https://learn.microsoft.com/zh-tw/legal/termsofuse)
* [商標](https://www.microsoft.com/legal/intellectualproperty/Trademarks/)
* © Microsoft 2025
