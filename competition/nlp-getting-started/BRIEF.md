# Competition brief — NLP with Disaster Tweets

* Kaggle: <https://www.kaggle.com/competitions/nlp-getting-started>
* Slug: `nlp-getting-started`
* Detected metric: `f1` (higher is better)
* Target column: `target`
* Score gate: `0.75`
* Gathered: 2026-10-19T10:55:53+00:00

## Files

| file | size (bytes) |
| --- | --- |
| `sample_submission.csv` | 22746 |
| `test.csv` | 420783 |
| `train.csv` | 987712 |

## Dataset profile

_No CSVs found._

## Problem statement

## Description

###Welcome to one of our "Getting Started" competitions 👋

This particular challenge is perfect for data scientists looking to get started with Natural Language Processing. The competition dataset is not too big, and even if you don’t have much personal computing power, you can do all of the work in our free, no-setup, Jupyter Notebooks environment called [Kaggle Notebooks](https://www.kaggle.com/docs/kernels#the-kernels-environment).

**If you want to talk with other users about this competition, come join our Discord! We've got channels for competitions, job postings and career discussions, resources, and socializing with your fellow data scientists. Follow the link here:** https://discord.gg/kaggle

###Competition Description

Twitter has become an important communication channel in times of emergency.
The ubiquitousness of smartphones enables people to announce an emergency they’re observing in real-time. Because of this, more agencies are interested in programatically monitoring Twitter (i.e. disaster relief organizations and news agencies).

But, it’s not always clear whether a person’s words are actually announcing a disaster. Take this example:

<img src="https://storage.googleapis.com/kaggle-media/competitions/tweet_screenshot.png" style= "float: left; width: 250px; margin-right:10px;">
<br><br>
The author explicitly uses the word “ABLAZE” but means it metaphorically. This is clear to a human right away, especially with the visual aid. But it’s less clear to a machine.

In this competition, you’re challenged to build a machine learning model that predicts which Tweets are about real disasters and which one’s aren’t. You’ll have access to a dataset of 10,000 tweets that were hand classified. If this is your first time working on an NLP problem, we've created a [quick tutorial](https://www.kaggle.com/philculliton/nlp-getting-started-tutorial) to get you up and running. 

Disclaimer: The dataset for this competition contains text that may be considered profane, vulgar, or offensive.

> ### 💡Getting Started Notebook
> To get started quickly, feel free to take advantage of [this starter notebook](https://www.kaggle.com/code/alexia/kerasnlp-starter-notebook-disaster-tweets).

###Acknowledgments

This dataset was created by the company figure-eight and originally shared on their [‘Data For Everyone’ website here](https://www.figure-eight.com/data-for-everyone/).

Tweet source: https://twitter.com/AnyOtherAnnaK/status/629195955506708480

## Evaluation

Submissions are evaluated using [F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html) between the predicted and expected answers.

F1 is calculated as follows:
$$
F_1 = 2 * \frac{precision * recall}{precision + recall}
$$

where:

$$
precision = \frac{TP}{TP + FP}
$$

$$
recall = \frac{TP}{TP + FN}
$$

and:

> True Positive [TP] = your prediction is 1, and the ground truth is also 1 - you predicted a _positive_ and that's _true_!
False Positive [FP] = your prediction is 1, and the ground truth is 0 - you predicted a _positive_, and that's _false_.
False Negative [FN] = your prediction is 0, and the ground truth is 1 - you predicted a _negative_, and that's _false_.

## Submission File
For each ID in the test set, you must predict 1 if the tweet is describing a real disaster, and 0 otherwise. The file should contain a header and have the following format:

> id,target
0,0
2,0
3,1
9,0
11,0

## data-description

## What files do I need?

You'll need **train.csv**, **test.csv** and **sample\_submission.csv**.

## What should I expect the data format to be?

Each sample in the train and test set has the following information:

*   The `text` of a tweet
*   A `keyword` from that tweet (although this may be blank!)
*   The `location` the tweet was sent from (may also be blank)

## What am I predicting?

You are predicting whether a given tweet is about a real disaster or not. If so, predict a `1`. If not, predict a `0`.


## Files

*   **train.csv** - the training set
*   **test.csv** - the test set
*   **sample_submission.csv** - a sample submission file in the correct format

## Columns

*   `id` - a unique identifier for each tweet
*   `text` - the text of the tweet
*   `location` - the location the tweet was sent from (may be blank)
*   `keyword` - a particular keyword from the tweet (may be blank)
*   `target` - in **train.csv** only, this denotes whether a tweet is about a real disaster (`1`) or not (`0`)

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
<p>Start Date: <strong>December 20, 2019</strong></p>
<p>End Date: <strong>This competition does not have an end date. </strong></p>

### COMPETITION-SPECIFIC TERMS

**COMPETITION TITLE**: Natural Language Processing with Disaster Tweets

**COMPETITION SPONSOR**: Kaggle

**COMPETITION SPONSOR ADDRESS**: 1600 Amphitheatre Pkwy, Mountain View, CA 94043

**COMPETITION WEBSITE**: https://www.kaggle.com/c/nlp-getting-started

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

## FAQ

### What is a Getting Started competition? 

Getting Started competitions were created by Kaggle data scientists for people who have little to no machine learning background. They are a great place to begin if you are new to data science or just finished a MOOC and want to get involved in Kaggle.

Getting Started competitions are a non-competitive way to get familiar with Kaggle’s platform, learn basic machine learning concepts, and start meeting people in the community. They have no cash prize and are on a rolling timeline.

### What’s the difference between a private and public leaderboard?

In this competition, because it is a Getting Started competition, there is no difference. We're scoring the entire test set on the Public Leaderboard. And we will refresh the competition every two months, so the Private Leaderboard is irrelevant.

For non-Getting Started Kaggle competitions, there is the concept of a public and private leaderboard to prevent participants from “overfitting” to the leaderboard. If your model is “overfit” to a dataset then it is not generalizable outside of the dataset you trained it on. This means that your model would have low accuracy on another sample of data taken from a similar dataset.

### Why are there perfect scores on the leaderboard?

This competition's test set labels are completely public. So it's likely that some participants will submit perfect submissions. Since there are no prizes, medals, or points associated with your leaderboard ranking in this competition, these scores have little consequence. The rankings are purely for the benefit of users to learn and see how their approach is improving. 

*"Then can you just clear them out? They're distracting."* It's a heavily time-intensive process to manage removals from a continuously live leaderboard. The threshold for what should be removed also becomes arbitrary -- if you remove 1.00 scores, then .99 scores will quickly appear. Since there is no prize consequence, we have chosen to leave the scores as an open sandbox.

### How do I create and manage a team?

When you accept the competition rules, a team will be created for you. You can invite others to your team, accept a merger with another team, and update basic information like team name by going to the [Team page](https://www.kaggle.com/c/nlp-getting-started/team).

We've heard from many Kagglers that teaming up is the best way to learn new skills AND have fun. If you don't have a teammate already, consider asking if anyone wants to team up in the [discussion forum](https://www.kaggle.com/c/nlp-getting-started/discussion).

### What are Notebooks?

Kaggle Notebooks is a cloud computational environment that enables reproducible and collaborative analysis. Kernels supports scripts in R and Python, Jupyter Notebooks, and RMarkdown reports. Go to the [Notebooks tab](https://www.kaggle.com/c/nlp-getting-started/notebooks) to view all of the publicly shared code on this competition. For more on how to use Notebooks to learn data science, visit Kaggle's [Learn Courses](https://www.kaggle.com/learn/overview).

### Why did my team disappear from the leaderboard?

To keep with the spirit of getting-started competitions, we have implemented a two month rolling window on submissions. Once a submission is more than two months old, it will be invalidated and no longer count towards the leaderboard.

If your team has no submissions in the previous two months, the team will also drop from the leaderboard. This will keep the leaderboard at a manageable size, freshen it up, and prevent newcomers from getting lost in a sea of abandoned scores.

*"I worked so hard to get that score! Give it back!"* Read more about our decision to implement rolling leaderboards, covered in the [Titanic Getting Started Competition forum here](https://www.kaggle.com/c/titanic/discussion/6240).

### How do I contact Support?

Kaggle does not have a dedicated support team so you’ll typically find that you receive a response more quickly by asking your question in the appropriate forum. (For this competition, you’ll want to use [this competition's discussion forum](https://www.kaggle.com/c/nlp-getting-started/discussion).

Support is only able to help with issues that are being experienced by all participants. Before contacting support, please check the discussion forum for information on your problem. If you can’t find it, you can post your problem in the forum so a fellow participant or a Kaggle team member can provide help. The forums are full of useful information on the data, metric, and different approaches. We encourage you to use the forums often. If you share your knowledge, you'll find that others will share a lot in turn!

If your problem persists or it seems to be effective all participants then please [contact us](https://www.kaggle.com/contact).
