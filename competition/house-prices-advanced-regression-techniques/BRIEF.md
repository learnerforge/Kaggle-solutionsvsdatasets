# Competition brief — house-prices-advanced-regression-techniques

* Kaggle: <https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques>
* Slug: `house-prices-advanced-regression-techniques`
* Detected metric: `rmse` (lower is better)
* Target column: `unknown`
* Score gate: `not set`
* Gathered: 2026-10-22T08:43:21+00:00

## Files

_No file list available (offline or not authenticated)._

## Dataset profile

_No CSVs found._

## Warnings

* Kaggle file list unavailable: `kaggle competitions files house-prices-advanced-regression-techniques --page-size` failed (exit 1): Authentication required to call the Kaggle API.

First, you will need a Kaggle account. You can sign up at
  https://www.kaggle.com/account/login

Recommended: log in with OAuth via a web-based authorization flow.
No token to manage; credentials are cached locally for you.
    kaggle auth login

If you'd rather not use OAuth, generate an API token at
  https://www.kaggle.com/settings/api  (click "Generate New Token" under "API")
and supply it to the CLI in one of these ways:

  Option A: Environment variable
    export KAGGLE_API_TOKEN=xxxxxxxxxxxxxx  # token copied from the settings UI

  Option B: API token file
    Save the token to ~/.kaggle/access_token
Hint: credentials missing or expired. Run `kaggle auth login` or set KAGGLE_USERNAME / KAGGLE_KEY (see engine/secrets.py).
* Dataset download failed: `kaggle competitions download house-prices-advanced-regression-techniques --path` failed (exit 1): Authentication required to call the Kaggle API.

First, you will need a Kaggle account. You can sign up at
  https://www.kaggle.com/account/login

Recommended: log in with OAuth via a web-based authorization flow.
No token to manage; credentials are cached locally for you.
    kaggle auth login

If you'd rather not use OAuth, generate an API token at
  https://www.kaggle.com/settings/api  (click "Generate New Token" under "API")
and supply it to the CLI in one of these ways:

  Option A: Environment variable
    export KAGGLE_API_TOKEN=xxxxxxxxxxxxxx  # token copied from the settings UI

  Option B: API token file
    Save the token to ~/.kaggle/access_token
Hint: credentials missing or expired. Run `kaggle auth login` or set KAGGLE_USERNAME / KAGGLE_KEY (see engine/secrets.py).

## Problem statement

# Problem statement — House Prices: Advanced Regression Techniques

> Fetched from Kaggle on 2026-10-19 10:55 UTC.
> Kaggle: https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques

## Description

<h3>Start here if...</h3>
<p>You have some experience&nbsp;with R or Python and&nbsp;machine learning basics. This is a perfect competition for data science students&nbsp;who have completed an online course in machine learning and are looking to expand their skill set before trying a featured competition.&nbsp;</p>
<div>
<h3>💡Getting Started Notebook</h3>
<p>To get started quickly, feel free to take advantage of <a href="https://www.kaggle.com/code/gusthema/house-prices-prediction-using-tfdf/notebook">this starter notebook</a>.</p>
</div>
<h3>Competition Description</h3>
<p><img src="https://storage.googleapis.com/kaggle-media/competitions/House%20Prices/kaggle_5407_media_housesbanner.png"></p>
<p>Ask a home buyer to describe their dream house, and they probably won't begin with the height of the basement ceiling or the proximity to an east-west railroad. But this playground competition's dataset proves that much more influences price negotiations than the number of bedrooms or a white-picket fence.</p>
<p>With 79 explanatory variables describing (almost) every aspect of residential homes in Ames, Iowa, this competition challenges you to predict the final price of each home.</p>
<h3>Practice Skills</h3>
<ul>
<li>Creative feature engineering&nbsp;</li>
<li>Advanced regression techniques like random forest and gradient boosting</li>
</ul>
<h2>Acknowledgments</h2>
<p>The <a href="https://jse.amstat.org/v19n3/decock.pdf" target="_blank">Ames Housing&nbsp;dataset</a>&nbsp;was compiled&nbsp;by Dean De Cock for use in data science education. It's an incredible alternative&nbsp;for data scientists looking for a modernized and expanded version of the often cited Boston Housing dataset.&nbsp;</p>

<p>Photo by <a href="https://unsplash.com/@tthfilms">Tom Thain</a> on Unsplash.</p>

## Evaluation

<h3>Goal</h3>
<p>It is your job to predict the sales price for each house.&nbsp;For each Id in the test set, you must predict the value of the SalePrice variable.&nbsp;</p>
<h3>Metric</h3>
<p>Submissions are evaluated on <a href="https://en.wikipedia.org/wiki/Root-mean-square_deviation" target="_blank">Root-Mean-Squared-Error (RMSE)</a>&nbsp;between the logarithm of the predicted value&nbsp;and the logarithm of the observed sales price. (Taking logs means that errors in predicting expensive houses and cheap houses will affect the result equally.)</p>
<h3>Submission File Format</h3>
<p>The file should contain a header and have the following format:</p>
<pre>Id,SalePrice<br>1461,169000.1<br>1462,187724.1233<br>1463,175221<br>etc.</pre>
<p>You can download an example submission file (sample_submission.csv) on the&nbsp;<a href="https://www.kaggle.com/c/house-prices-advanced-regression-techniques/data" target="_blank">Data page.</a></p>

## data-description

<h2>File descriptions</h2>

<ul>

<li><strong>train.csv</strong> - the training set</li>

<li><strong>test.csv</strong> - the test set</li>

<li><strong>data_description.txt</strong> - full description of each column, originally prepared by Dean De Cock but lightly edited to match the column names used here</li>

<li><strong>sample_submission.csv</strong> - a benchmark submission from a linear regression on year and month of sale, lot square footage, and number of bedrooms</li>

</ul>

<h2>Data fields</h2>

<p>Here's a brief version of what you'll find in the data description file.</p>

<ul>

<li><strong>SalePrice</strong> - the property's sale price in dollars. This is the target variable that you're trying to predict.</li>

<li><strong>MSSubClass</strong>: The building class</li>

<li><strong>MSZoning</strong>: The general zoning classification</li>

<li><strong>LotFrontage</strong>: Linear feet of street connected to property</li>

<li><strong>LotArea</strong>: Lot size in square feet</li>

<li><strong>Street</strong>: Type of road access</li>

<li><strong>Alley</strong>: Type of alley access</li>

<li><strong>LotShape</strong>: General shape of property</li>

<li><strong>LandContour</strong>: Flatness of the property</li>

<li><strong>Utilities</strong>: Type of utilities available</li>

<li><strong>LotConfig</strong>: Lot configuration</li>

<li><strong>LandSlope</strong>: Slope of property</li>

<li><strong>Neighborhood</strong>: Physical locations within Ames city limits</li>

<li><strong>Condition1</strong>: Proximity to main road or railroad</li>

<li><strong>Condition2</strong>: Proximity to main road or railroad (if a second is present)</li>

<li><strong>BldgType</strong>: Type of dwelling</li>

<li><strong>HouseStyle</strong>: Style of dwelling</li>

<li><strong>OverallQual</strong>: Overall material and finish quality</li>

<li><strong>OverallCond</strong>: Overall condition rating</li>

<li><strong>YearBuilt</strong>: Original construction date</li>

<li><strong>YearRemodAdd</strong>: Remodel date</li>

<li><strong>RoofStyle</strong>: Type of roof</li>

<li><strong>RoofMatl</strong>: Roof material</li>

<li><strong>Exterior1st</strong>: Exterior covering on house</li>

<li><strong>Exterior2nd</strong>: Exterior covering on house (if more than one material)</li>

<li><strong>MasVnrType</strong>: Masonry veneer type</li>

<li><strong>MasVnrArea</strong>: Masonry veneer area in square feet</li>

<li><strong>ExterQual</strong>: Exterior material quality</li>

<li><strong>ExterCond</strong>: Present condition of the material on the exterior</li>

<li><strong>Foundation</strong>: Type of foundation</li>

<li><strong>BsmtQual</strong>: Height of the basement</li>

<li><strong>BsmtCond</strong>: General condition of the basement</li>

<li><strong>BsmtExposure</strong>: Walkout or garden level basement walls</li>

<li><strong>BsmtFinType1</strong>: Quality of basement finished area</li>

<li><strong>BsmtFinSF1</strong>: Type 1 finished square feet</li>

<li><strong>BsmtFinType2</strong>: Quality of second finished area (if present)</li>

<li><strong>BsmtFinSF2</strong>: Type 2 finished square feet</li>

<li><strong>BsmtUnfSF</strong>: Unfinished square feet of basement area</li>

<li><strong>TotalBsmtSF</strong>: Total square feet of basement area</li>

<li><strong>Heating</strong>: Type of heating</li>

<li><strong>HeatingQC</strong>: Heating quality and condition</li>

<li><strong>CentralAir</strong>: Central air conditioning</li>

<li><strong>Electrical</strong>: Electrical system</li>

<li><strong>1stFlrSF</strong>: First Floor square feet</li>

<li><strong>2ndFlrSF</strong>: Second floor square feet</li>

<li><strong>LowQualFinSF</strong>: Low quality finished square feet (all floors)</li>

<li><strong>GrLivArea</strong>: Above grade (ground) living area square feet</li>

<li><strong>BsmtFullBath</strong>: Basement full bathrooms</li>

<li><strong>BsmtHalfBath</strong>: Basement half bathrooms</li>

<li><strong>FullBath</strong>: Full bathrooms above grade</li>

<li><strong>HalfBath</strong>: Half baths above grade</li>

<li><strong>Bedroom</strong>: Number of bedrooms above basement level</li>

<li><strong>Kitchen</strong>: Number of kitchens</li>

<li><strong>KitchenQual</strong>: Kitchen quality</li>

<li><strong>TotRmsAbvGrd</strong>: Total rooms above grade (does not include bathrooms)</li>

<li><strong>Functional</strong>: Home functionality rating</li>

<li><strong>Fireplaces</strong>: Number of fireplaces</li>

<li><strong>FireplaceQu</strong>: Fireplace quality</li>

<li><strong>GarageType</strong>: Garage location</li>

<li><strong>GarageYrBlt</strong>: Year garage was built</li>

<li><strong>GarageFinish</strong>: Interior finish of the garage</li>

<li><strong>GarageCars</strong>: Size of garage in car capacity</li>

<li><strong>GarageArea</strong>: Size of garage in square feet</li>

<li><strong>GarageQual</strong>: Garage quality</li>

<li><strong>GarageCond</strong>: Garage condition</li>

<li><strong>PavedDrive</strong>: Paved driveway</li>

<li><strong>WoodDeckSF</strong>: Wood deck area in square feet</li>

<li><strong>OpenPorchSF</strong>: Open porch area in square feet</li>

<li><strong>EnclosedPorch</strong>: Enclosed porch area in square feet</li>

<li><strong>3SsnPorch</strong>: Three season porch area in square feet</li>

<li><strong>ScreenPorch</strong>: Screen porch area in square feet</li>

<li><strong>PoolArea</strong>: Pool area in square feet</li>

<li><strong>PoolQC</strong>: Pool quality</li>

<li><strong>Fence</strong>: Fence quality</li>

<li><strong>MiscFeature</strong>: Miscellaneous feature not covered in other categories</li>

<li><strong>MiscVal</strong>: $Value of miscellaneous feature</li>

<li><strong>MoSold</strong>: Month Sold</li>

<li><strong>YrSold</strong>: Year Sold</li>

<li><strong>SaleType</strong>: Type of sale</li>

<li><strong>SaleCondition</strong>: Condition of sale</li>

</ul>

## rules

### One account per participant

You cannot sign up to Kaggle from multiple accounts and therefore you cannot submit from multiple accounts.

### No private sharing outside teams

Privately sharing code or data outside of teams is not permitted. It's okay to share code if made available to all participants on the forums.

### Team Mergers

Team mergers are allowed and can be performed by the team leader. In order to merge, the combined team must have a total submission count less than or equal to the maximum allowed as of the Team Merger Deadline. The maximum allowed is the number of submissions per day multiplied by the number of days the competition has been running.

### Team Limits

The maximum team size is 10.

### Submission Limits

You may submit a maximum of 10 entries per day.

You may select up to 2 final submissions for judging.

### Competition Timeline
<p>Start Date: <strong>8/30/2016 1:08 AM UTC</strong></p>
<p>End Date: <strong>This competition does not have an end date. </strong></p>

### COMPETITION-SPECIFIC TERMS

**COMPETITION TITLE**: House Prices - Advanced Regression Techniques

**COMPETITION SPONSOR**: Kaggle

**COMPETITION SPONSOR ADDRESS**: 1600 Amphitheatre Pkwy, Mountain View, CA 94043

**COMPETITION WEBSITE**: https://www.kaggle.com/c/house-prices-advanced-regression-techniques

**DATA ACCESS AND USE**: Competition Use and Academic, Non-Commercial Use Only

<ul>
<li><span style="font-size: 1em; line-height: 1.5em;">Due to the public nature of the data, this competition does not count towards Kaggle ranking points.</span></li>
<li><span style="font-size: 1em; line-height: 1.5em;">We ask that you respect the spirit of the competition and do not cheat. Hand-labeling is forbidden.</span></li>
</ul>

Competitions are open to residents of the United States and worldwide, except that if you are a resident of Crimea, so-called Donetsk People's Republic (DNR) or Luhansk People's Republic (LNR), Cuba, Iran, Syria, or North Korea or are subject to U.S. export controls or sanctions, you may not enter the Competition. Other local rules and regulations may apply to you, so please check your local laws to ensure that you are eligible to participate in skills-based competitions. The Competition Host reserves the right to forego or award alternative Prizes where needed to comply with local laws. If a winner is located in a country where prizes cannot be awarded then they are not eligible to receive a prize.

**ENTRY IN THIS COMPETITION CONSTITUTES YOUR ACCEPTANCE OF THESE OFFICIAL COMPETITION RULES.**

The Competition named above is a skills-based competition to promote and further the field of data science. You must register via the Competition Website to enter. Your competition submissions ("Submissions") must conform to the requirements stated on the Competition Website. Your Submissions will be scored based on the evaluation metric described on the Competition Website. Subject to compliance with the Competition Rules, Prizes, if any, will be awarded to participants with the best scores, based on the merits of the data science models submitted. See below for the complete Competition Rules.

### A. COMPETITION-SPECIFIC RULES

In addition to the provisions of the General Competition Rules below, you understand and agree to these Competition-Specific Rules required by the Competition Sponsor:

#### **1. AUTOMATED MACHINE LEARNING TOOLS (AMLT).** 

Individual participants and Teams may use automated machine learning tool(s) (“AMLT”) (e.g., Google AutoML, H2O Driverless AI, etc.) to create a Submission, provided that the participant or Team ensures that they have an appropriate license to the AMLT such that they are able to comply with the Competition Rules. 

### B. GENERAL COMPETITION RULES
#### **1.	BINDING AGREEMENT.** 

To enter the Competition, you must agree to these Official Competition Rules, which incorporate by reference the provisions and content of the Competition Website and any Specific Competition Rules above (collectively, the "Rules"). Please read these Rules carefully before entry to ensure you understand and agree. You further agree that submission of an entry in the Competition constitutes agreement to these Rules. You may not submit an entry to the Competition and are not eligible to receive the prizes associated with this Competition (“Prizes”) unless you agree to these Rules. These Rules form a binding legal agreement between you and the Competition Sponsor with respect to the Competition.

#### **2.	ELIGIBILITY.** 

A. To be eligible to enter the Competition, you must be:
	(i) a registered account holder at Kaggle.com; 
	(ii) the older of 18 years old or the age of majority in your jurisdiction of residence (unless otherwise agreed to by Competition Sponsor and appropriate parental/guardian consents have been obtained by Competition Sponsor); 
	(iii) not a resident of Crimea, so-called Donetsk People's Republic (DNR) or Luhansk People's Republic (LNR), Cuba, Iran, Syria, or North Korea; and
	(iv) not a person or representative of an entity under U.S. export controls or sanctions (see [https://www.treasury.gov/resource-center/sanctions/Programs/Pages/Programs.aspx][1]).

If you are entering as a representative of a company, educational institution or other legal entity, or on behalf of your employer, these rules are binding on you, individually, and the entity you represent or are an employee. If you are acting within the scope of your employment, as an employee, contractor, or agent of another party, you warrant that such party has full knowledge of your actions and has consented thereto, including your potential receipt of a Prize. You further warrant that your actions do not violate your employer's or entity's policies and procedures.   

The Competition Sponsor reserves the right to verify eligibility and to adjudicate on any dispute at any time. If you provide any false information relating to the Competition concerning your identity, residency, mailing address, telephone number, email address, ownership of right, or information required for entering the Competition, you may be immediately disqualified from the Competition.

B. Unless otherwise stated in the Specific Competition Rules above or prohibited by internal policies of the Competition Entities, employees, interns, contractors, officers and directors of Competition Entities may enter and participate in the Competition, but are not eligible to win any Prizes. "Competition Entities" means the Competition Sponsor, Kaggle Inc., and their respective parent companies, subsidiaries and affiliates. If you are such a participant from a Competition Entity, you are subject to all applicable internal policies of your employer with respect to your participation.

#### **3.	SPONSOR AND HOSTING PLATFORM.** 

The Competition is sponsored by Competition Sponsor named above. The Competition is hosted on behalf of Competition Sponsor by Kaggle Inc. ("Kaggle"). Kaggle is an independent contractor of Competition Sponsor, and is not a party to this or any agreement between you and Competition Sponsor. You understand that Kaggle has no responsibility with respect to selecting the potential Competition winner(s) or awarding any Prizes. Kaggle will perform certain administrative functions relating to hosting the Competition, and you agree to abide by the provisions relating to Kaggle under these Rules. As a Kaggle.com account holder and user of the Kaggle competition platform, remember you have accepted and are subject to the Kaggle Terms of Service at [www.kaggle.com/terms][2] in addition to these Rules.

#### **4.	COMPETITION PERIOD.** 

For the purposes of Prizes, the Competition will run from the Start Date and time to the Final Submission Deadline (such duration the “Competition Period”). The Competition Timeline is subject to change, and Competition Sponsor may introduce additional hurdle deadlines during the Competition Period. Any updated or additional deadlines will be publicized on the Competition Website. It is your responsibility to check the Competition Website regularly to stay informed of any deadline changes. *YOU ARE RESPONSIBLE FOR DETERMINING THE CORRESPONDING TIME ZONE IN YOUR LOCATION.* 

#### **5.	COMPETITION ENTRY.** 

NO PURCHASE NECESSARY TO ENTER OR WIN. To enter the Competition, you must register on the Competition Website prior to the Entry Deadline, and follow the instructions for developing and entering your Submission through the Competition Website. Your Submissions must be made in the manner and format, and in compliance with all other requirements, stated on the Competition Website (the "Requirements"). Submissions must be received before any Submission deadlines stated on the Competition Website. Submissions not received by the stated deadlines will not be eligible to receive a Prize.

Submissions may not use or incorporate information from hand labeling or human prediction of the validation dataset or test data records.

If the Competition is a multi-stage competition with temporally separate training and/or test data, one or more valid Submissions may be required during each Competition stage in the manner described on the Competition Website in order for the Submissions to be Prize eligible.

Submissions are void if they are in whole or part illegible, incomplete, damaged, altered, counterfeit, obtained through fraud, or late. Competition Sponsor reserves the right to disqualify any entrant who does not follow these Rules, including making a Submission that does not meet the Requirements. 

#### **6.	INDIVIDUALS AND TEAMS.** 

A. *Individual Account*. You may make Submissions only under one, unique Kaggle.com account. You will be disqualified if you make Submissions through more than one Kaggle account, or attempt to falsify an account to act as your proxy. You may submit up to the maximum number of Submissions per day as specified on the Competition Website. 

B. *Teams*. If permitted under the Competition Website guidelines, multiple individuals may collaborate as a team (a "Team"); however, you may join or form only one Team. Each Team member must be a single individual with a separate Kaggle account. You must register individually for the Competition before joining a Team. You must confirm your Team membership to make it official by responding to the Team notification message sent to your Kaggle account. Team membership may not exceed the Maximum Team Size stated on the Competition Website.

C. *Team Merger*. Teams may request to merge via the Competition Website. Team mergers may be allowed provided that: (i) the combined Team does not exceed the Maximum Team Size; (ii) the number of Submissions made by the merging Teams does not exceed the number of Submissions permissible for one Team at the date of the merger request; (iii) the merger is completed before the earlier of: any merger deadline or the Competition deadline; and (iv) the proposed combined Team otherwise meets all the requirements of these Rules. 

#### **7.	COMPETITION DATA.** 

"Competition Data" means the data or datasets available from the Competition Website for the purpose of use in the Competition, including any prototype or executable code provided on the Competition Website. The Competition Data will contain private and public test sets. Which data belongs to which set will not be made available to participants. 

A. *Data Access and Use*. You may access and use the Competition Data for non-commercial purposes only, including for participating in the Competition and on Kaggle.com forums, and for academic research and education. The Competition Sponsor reserves the right to disqualify any participant who uses the Competition Data other than as permitted by the Competition Website and these Rules.

B. *Data Security*. You agree to use reasonable and suitable measures to prevent persons who have not formally agreed to these Rules from gaining access to the Competition Data. You agree not to transmit, duplicate, publish, redistribute or otherwise provide or make available the Competition Data to any party not participating in the Competition. You agree to notify Kaggle immediately upon learning of any possible unauthorized transmission of or unauthorized access to the Competition Data and agree to work with Kaggle to rectify any unauthorized transmission or access.

C. *External Data*. You may use data other than the Competition Data (“External Data”) to develop and test your Submissions. However, you will ensure the External Data is publicly available and equally accessible to use by all participants of the Competition for purposes of the competition at no cost to the other participants. The ability to use External Data under this Section 7.C (External Data) does not limit your other obligations under these Competition Rules, including but not limited to Section 11 (Winners Obligations). 

#### **8.	SUBMISSION CODE REQUIREMENTS.**

A. *Private Code Sharing*. Unless otherwise specifically permitted under the Competition Website or Competition Specific Rules above, during the Competition Period, you are not allowed to privately share source or executable code developed in connection with or based upon the Competition Data or other source or executable code relevant to the Competition (“Competition Code”). This prohibition includes sharing Competition Code between separate Teams, unless a Team merger occurs. Any such sharing of Competition Code is a breach of these Competition Rules and may result in disqualification.

B. *Public Code Sharing*. You are permitted to publicly share Competition Code, provided that such public sharing does not violate the intellectual property rights of any third party. If you do choose to share Competition Code or other such code, you are required to share it on Kaggle.com on the discussion forum or notebooks associated specifically with the Competition for the benefit of all competitors. By so sharing, you are deemed to have licensed the shared code under an Open Source Initiative-approved license (see [www.opensource.org][3]) that in no event limits commercial use of such Competition Code or model containing or depending on such Competition Code.

C. *Use of Open Source*. Unless otherwise stated in the Specific Competition Rules above, if open source code is used in the model to generate the Submission, then you must only use open source code licensed under an Open Source Initiative-approved license (see [www.opensource.org][4]) that in no event limits commercial use of such code or model containing or depending on such code.

#### **9.	DETERMINING LEADERBOARD.** 

Each Submission will be scored and ranked by the evaluation metric stated on the Competition Website. During the Competition Period, the current ranking will be visible on the Competition Website's public leaderboard. The public leaderboard will be based on the public test set and the private leaderboard will be based on the private test set.

In the event of a tie, the Submission that was entered first to the Competition will be ranked higher.


Once a submission is more than two months old, it will be invalidated and no longer count towards the leaderboard. If a team has no submissions in the previous two months, the team will also drop from the leaderboard. 

#### **10.	DISQUALIFICATION.**

Competition Sponsor reserves the right to disqualify any participant from the Competition if the Competition Sponsor reasonably believes that the participant has attempted to undermine the legitimate operation of the Competition by cheating, deception, or other unfair playing practices or abuses, threatens or harasses any other participants, Competition Sponsor or Kaggle.
 
A disqualified participant may be removed from the Competition leaderboard, at Kaggle's sole discretion.
 
The competition has no specified end date, and therefore there is no final leaderboard. In the event the sponsor chooses to conclude the competition, the final leaderboard list will be publicly displayed at Kaggle.com. Determinations of Competition Sponsor are final and binding.

#### **11.	GENERAL CONDITIONS.**  

All federal, state, provincial and local laws and regulations apply.   

#### **12.	PUBLICITY.**

You agree that Competition Sponsor, Kaggle and its affiliates may use your name and likeness for advertising and promotional purposes without additional compensation, unless prohibited by law.

#### **13.	PRIVACY.**

You acknowledge and agree that Competition Sponsor and Kaggle may collect, store, share and otherwise use personally identifiable information provided by you during the Kaggle account registration process and the Competition, including but not limited to, name, mailing address, phone number, and email address (“Personal Information”). Kaggle acts as an independent controller with regard to its collection, storage, sharing, and other use of this Personal Information, and will use this Personal Information in accordance with its Privacy Policy <[www.kaggle.com/privacy][6]>, including for administering the Competition. As a Kaggle.com account holder, you have the right to request access to, review, rectification, portability or deletion of any personal data held by Kaggle about you by logging into your account and/or contacting Kaggle Support at <[www.kaggle.com/contact][7]>.

 As part of Competition Sponsor performing this contract between you and the Competition Sponsor, Kaggle will transfer your Personal Information to Competition Sponsor, which acts as an independent controller with regard to this Personal Information. As a controller of such Personal Information, Competition Sponsor agrees to comply with all U.S. and foreign data protection obligations with regard to your Personal Information. Kaggle will transfer your Personal Information to Competition Sponsor in the country specified in the Competition Sponsor Address listed above, which may be a country outside the country of your residence. Such country may not have privacy laws and regulations similar to those of the country of your residence.

#### **14.	WARRANTY, INDEMNITY AND RELEASE.** 

You warrant that your Submission is your own original work and, as such, you are the sole and exclusive owner and rights holder of the Submission, and you have the right to make the Submission and grant all required licenses.  You agree not to make any Submission that: (i) infringes any third party proprietary rights, intellectual property rights, industrial property rights, personal or moral rights or any other rights, including without limitation, copyright, trademark, patent, trade secret, privacy, publicity or confidentiality obligations, or defames any person; or (ii) otherwise violates any applicable U.S. or foreign state or federal law.

To the maximum extent permitted by law, you indemnify and agree to keep indemnified Competition Entities at all times from and against any liability, claims, demands, losses, damages, costs and expenses resulting from any of your acts, defaults or omissions and/or a breach of any warranty set forth herein. To the maximum extent permitted by law, you agree to defend, indemnify and hold harmless the Competition Entities from and against any and all claims, actions, suits or proceedings, as well as any and all losses, liabilities, damages, costs and expenses (including reasonable attorneys fees) arising out of or accruing from: (a) your Submission or other material uploaded or otherwise provided by you that infringes any third party proprietary rights, intellectual property rights, industrial property rights, personal or moral rights or any other rights, including without limitation, copyright, trademark, patent, trade secret, privacy, publicity or confidentiality obligations, or defames any person; (b) any misrepresentation made by you in connection with the Competition; (c) any non-compliance by you with these Rules or any applicable U.S. or foreign state or federal law; (d) claims brought by persons or entities other than the parties to these Rules arising from or related to your involvement with the Competition; and (e) your acceptance, possession, misuse or use of any Prize, or your participation in the Competition and any Competition-related activity.

You hereby release Competition Entities from any liability associated with: (a) any malfunction or other problem with the Competition Website; (b) any error in the collection, processing, or retention of any Submission; or (c) any typographical or other error in the printing, offering or announcement of any Prize or winners.

#### **15.	INTERNET.** 

Competition Entities are not responsible for any malfunction of the Competition Website or any late, lost, damaged, misdirected, incomplete, illegible, undeliverable, or destroyed Submissions or entry materials due to system errors, failed, incomplete or garbled computer or other telecommunication transmission malfunctions, hardware or software failures of any kind, lost or unavailable network connections, typographical or system/human errors and failures, technical malfunction(s) of any telephone network or lines, cable connections, satellite transmissions, servers or providers, or computer equipment, traffic congestion on the Internet or at the Competition Website, or any combination thereof, which may limit a participant’s ability to participate.

#### **16.	RIGHT TO CANCEL, MODIFY OR DISQUALIFY.**

If for any reason the Competition is not capable of running as planned, including infection by computer virus, bugs, tampering, unauthorized intervention, fraud, technical failures, or any other causes which corrupt or affect the administration, security, fairness, integrity, or proper conduct of the Competition, Competition Sponsor reserves the right to cancel, terminate, modify or suspend the Competition. Competition Sponsor further reserves the right to disqualify any participant who tampers with the submission process or any other part of the Competition or Competition Website.  Any attempt by a participant to deliberately damage any website, including the Competition Website, or undermine the legitimate operation of the Competition is a violation of criminal and civil laws. Should such an attempt be made, Competition Sponsor and Kaggle each reserves the right to seek damages from any such participant to the fullest extent of the applicable law.

#### **17.	NOT AN OFFER OR CONTRACT OF EMPLOYMENT.**

Under no circumstances will the entry of a Submission, the awarding of a Prize, or anything in these Rules be construed as an offer or contract of employment with Competition Sponsor or any of the Competition Entities. You acknowledge that you have submitted your Submission voluntarily and not in confidence or in trust. You acknowledge that no confidential, fiduciary, agency, employment or other similar relationship is created between you and Competition Sponsor or any of the Competition Entities by your acceptance of these Rules or your entry of your Submission.

#### **18.	GOVERNING LAW.** 

Unless otherwise provided in the Competition Specific Rules above, all claims arising out of or relating to these Rules will be governed by California law, excluding its conflict of laws rules, and will be litigated exclusively in the Federal or State courts of Santa Clara County, California, USA. The parties consent to personal jurisdiction in those courts. If any provision of these Rules is held to be invalid or unenforceable, all remaining provisions of the Rules will remain in full force and effect.


  [1]: https://www.treasury.gov/resource-center/sanctions/Programs/Pages/Programs.aspx
  [2]: http://www.kaggle.com/terms
  [3]: http://www.opensource.org
  [4]: http://www.opensource.org
  [5]: https://www.kaggle.com/WinningModelDocumentationGuidelines
  [6]: http://www.kaggle.com/privacy
  [7]: http://www.kaggle.com/contact

## Tutorials

<h3>Kaggle Learn</h3>
<p><a href="https://www.kaggle.com/learn" target="_blank"><b>Kaggle Learn</b></a> offers hands-on courses for most data science topics. These short courses prepare you with the key ideas to build your own projects. </p>
<p>The <a href="https://www.kaggle.com/learn/machine-learning" target="_blank"><b>Machine Learning Course</b></a> will give you everything you need to succeed in this competition and others like it.</p> 

<h3>Other R Tutorials</h3>

<b><a href="https://www.kaggle.com/skirmer/house-prices-advanced-regression-techniques/fun-with-real-estate-data" target="_blank">Fun with Real Estate Data</a></b>
<ul> 
<li>Use Rmarkdown to learn advanced regression techniques like random forests and  <a href="https://github.com/dmlc/xgboost" target="_blank">XGBoost</a>
</li></ul> 

<b><a href="https://www.kaggle.com/jiashenliu/house-prices-advanced-regression-techniques/updated-xgboost-with-parameter-tuning/run/362252" target="_blank">XGBoost with Parameter Tuning</a></b>
<ul>
<li>Implement LASSO regression to avoid multicollinearity
</li><li>Includes linear regression, random forest, and <a href="https://github.com/dmlc/xgboost" target="_blank">XGBoost</a> models as well</li>
</ul>

<b><a href="https://www.kaggle.com/jimthompson/house-prices-advanced-regression-techniques/ensemble-model-stacked-model-example" target="_blank">Ensemble Modeling: Stack Model Example</a></b>
<ul> 
<li>Use "<a href="http://mlwave.com/kaggle-ensembling-guide/" target="_blank">ensembling</a>" to combine the predictions of several models
</li><li>Includes GBM (gradient boosting machine),  <a href="https://github.com/dmlc/xgboost" target="_blank">XGBoost</a>, ranger, and neural net using the <a href="https://cran.r-project.org/web/packages/caret/index.html" target="_blank">caret package</a>
</li></ul>

<b><a href="https://www.kaggle.com/ozagordi/house-prices-advanced-regression-techniques/a-clear-example-of-overfitting" target="_blank">A Clear Example of Overfitting</a></b>
<ul> 
<li>Learn about the dreaded consequences of overfitting data
</li></ul>

<h3>Other Python Tutorials</h3>
<b><a href="https://www.kaggle.com/pmarcelino/house-prices-advanced-regression-techniques/comprehensive-data-exploration-with-python" target="_blank">Comprehensive Data Exploration with Python</a></b>
<ul> 
<li>Understand how variables are distributed and how they interact 
</li><li>Apply different transformations before training machine learning models
</li></ul>

<b><a href="https://www.kaggle.com/dgawlik/house-prices-advanced-regression-techniques/house-prices-eda" target="_blank">House Prices EDA</a></b>
<ul> 
<li>Learn to use visualization techniques to study missing data and distributions 
</li><li>Includes correlation heatmaps, pairplots, and t-SNE to help inform appropriate inputs to a linear model
</li></ul>

<b><a href="https://www.kaggle.com/juliencs/house-prices-advanced-regression-techniques/a-study-on-regression-applied-to-the-ames-dataset" target="_blank">A Study on Regression Applied to the Ames Dataset</a></b>
<ul>
<li>Demonstrate effective tactics for feature engineering 
</li><li>Explore linear regression with different regularization methods including ridge, LASSO, and ElasticNet using <a href="http://blog.kaggle.com/author/kevin-markham/" target="_blank">scikit-learn</a>
</li></ul>

<b><a href="https://www.kaggle.com/apapiu/house-prices-advanced-regression-techniques/regularized-linear-models" target="_blank">Regularized Linear Models</a></b>
<ul> 
<li>Build a basic linear model 
</li><li>Try more advanced algorithms including <a href="https://github.com/dmlc/xgboost" target="_blank">XGBoost</a> and neural nets using <a href="https://keras.io/" target="_blank">Keras</a>
</li></ul>

## Frequently Asked Questions

<h3>What is a Getting Started competition? </h3>

<p>Getting Started competitions were created by Kaggle data scientists for people who have little to no machine learning background. They are a great place to begin if you are new to data science or just finished a MOOC and want to get involved in Kaggle.</p>

<p>Getting Started competitions are a non-competitive way to get familiar with Kaggle’s platform, learn basic machine learning concepts, and start meeting people in the community. They have no cash prize and are on a rolling timeline. </p>

<h3>What’s the difference between a private and public leaderboard?</h3>

<p>The Kaggle leaderboard has a public and private component to prevent participants from “overfitting” to the leaderboard. If your model is “overfit” to a dataset then it is not generalizable outside of the dataset you trained it on. This means that your model would have low accuracy on another sample of data taken from a similar dataset.</p>

<b>Public Leaderboard</b>
<p>For all participants, the same 50% of predictions from the test set are assigned to the public leaderboard. The score you see on the public leaderboard reflects your model’s accuracy on this portion of the test set. </p>

<b>Private Leaderboard</b>
<p>The other 50% of predictions from the test set are assigned to the private leaderboard. The private leaderboard is not visible to participants until the competition has concluded. At the end of a competition, we will reveal the private leaderboard so you can see your score on the other 50% of the test data. The scores on the private leaderboard are used to determine the competition winners. Getting Started competitions are run on a rolling timeline so the private leaderboard is never revealed.</p>

<h3>How do I create and manage a team?</h3>
<p>When you accept the competition rules, a team will be created for you. You can invite others to your team, accept a merger with another team, and update basic information like team name by going to the More &lt; <a href="https://www.kaggle.com/c/house-prices-advanced-regression-techniques/team" target="_blank">Team</a> page.</p>

<p>We've heard from many Kagglers that teaming up is the best way to learn new skills AND have fun. If you don't have a teammate already, consider asking if anyone wants to team up in the <a href="https://www.kaggle.com/c/house-prices-advanced-regression-techniques/discussion" target="_blank">discussion forum</a>. </p>

<h3>What are kernels?</h3>

<p>Kaggle Kernels is a cloud computational environment that enables reproducible and collaborative analysis. Kernels supports scripts in R and Python, Jupyter Notebooks, and RMarkdown reports. Go to the <a href="https://www.kaggle.com/c/house-prices-advanced-regression-techniques/kernels" target="_blank">Kernels tab</a> to view all of the publicly shared code on this competition. For more on how to use Kernels to learn data science, visit the <a href="https://www.kaggle.com/c/house-prices-advanced-regression-techniques/overview/tutorials" target="_blank&gt;Tutorials tab&lt;/a&gt;.&lt;/p&gt;

&lt;h3&gt;Why did my team disappear from the leaderboard?&lt;/h3&gt;
&lt;p&gt;To keep with the spirit of getting-started competitions, we have implemented a two month rolling window on submissions. Once a submission is more than two months old, it will be invalidated and no longer count towards the leaderboard.&lt;/p&gt;
&lt;p&gt;If your team has no submissions in the previous two months, the team will also drop from the leaderboard. This will keep the leaderboard at a manageable size, freshen it up, and prevent newcomers from getting lost in a sea of abandoned scores.&lt;/p&gt;
&lt;p&gt;&lt;i&gt;"> Read more about our decision to implement a rolling leaderboard on getting started competitions </a><a href="https://www.kaggle.com/c/titanic/discussion/6240" target="_blank">here</a>.</p>

<h3>How do I contact Support?</h3>
<p>Kaggle does not have a dedicated support team so you’ll typically find that you receive a response more quickly by asking your question in the appropriate forum. (For this competition, you’ll want to use the <a href="https://www.kaggle.com/c/house-prices-advanced-regression-techniques/discussion" target="_blank">House Prices discussion forum</a>). </p>

<p>Support is only able to help with issues that are being experienced by all participants. Before contacting support, please check the discussion forum for information on your problem. If you can’t find it, you can post your problem in the forum so a fellow participant or a Kaggle team member can provide help. The forums are full of useful information on the data, metric, and different approaches. We encourage you to use the forums often. If you share your knowledge, you'll find that others will share a lot in turn!</p>

<p>If your problem persists or it seems to be affecting all participants then please <a href="https://www.kaggle.com/contact" target="_blank">contact us</a>.</p>
