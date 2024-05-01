import unittest
import library.utils as utils


class TestFilters(unittest.TestCase):

    def test_filter_tokens_bill(self):
        email, expected = Fixtures.bill
        filtered, map = utils.Utils.filter_tokens(email)
        self.assertEqual(filtered.split("\n"), expected.split("\n"))
        
        self.assertEqual(map["/0"], "/?qs=ca7315dfe9ecf24871e90dc4ba068c5bb1a2877b649e24bc62abe98408aa746ae3ab31a17cef8fbfcdc55e5bd0e1a257cc1c4ac3b69456f2ad2ffd60bc377b3a")
        self.assertEqual(map["/23"], "/?qs=ca7315dfe9ecf248c7dee0a7f0d05b4203a6e1877326cc7bb9402cbfd321a0f3c2f183e3363d20e0f381e2af273f7147543c5691549ca8ebba57b9687d02a42d")

    def test_filter_tokens_bill(self):
        email, expected = Fixtures.newsletter
        filtered, map = utils.Utils.filter_tokens(email)
        self.assertEqual(filtered.split("\n"), expected.split("\n"))
        
        self.assertEqual(map["/0"], "/comm/jobs/view/3895695518/?trackingId=b%2BnFD4EalrLKZ4XyS4QvQg%3D%3D&refId=ByteString%28length%3D16%2Cbytes%3D9cb9191d...613fc476%29&lipi=urn%3Ali%3Apage%3Aemail_email_job_alert_digest_01%3B%2FqiVQpxoRkSa9DgLVSm7EQ%3D%3D&midToken=AQHOmWZkzlO39Q&midSig=3vtYihGNMCFHc1&trk=eml-email_job_alert_digest_01-job_card-0-view_job&trkEmail=eml-email_job_alert_digest_01-job_card-0-view_job-null-2l9y4~luykrlt2~t-null-null&eid=2l9y4-luykrlt2-t&otpToken=MTYwNjFiZTExYjJlYzljZWI1MjkwNGU5NDYxYWU2YjI4N2M4ZDA0NDllYTQ4YjZkNzljMzA1NmU0ZjU5NWRmOWYyZDA4NGJlNGZjN2MxZTc0NzQ3MmI3Yzk1N2FlOGQxMjUyYzY2NTYzMDA0YmI1YSwxLDE%3D")
 
    def test_filter_tokens_general(self):
        email, expected = Fixtures.general
        filtered, map = utils.Utils.filter_tokens(email)
        self.assertEqual(filtered.split("\n"), expected.split("\n"))
        
        self.assertEqual(map["/0"], "/careers")
 

    

class Fixtures:

    newsletter = """
Your job alert for head of engineering in Boulder


13 new jobs match your preferences.

Vice President of Engineering
Signify Technology
United States
This company is actively hiring
Apply with resume & profile
View job: https://www.linkedin.com/comm/jobs/view/3895695518/?trackingId=b%2BnFD4EalrLKZ4XyS4QvQg%3D%3D&refId=ByteString%28length%3D16%2Cbytes%3D9cb9191d...613fc476%29&lipi=urn%3Ali%3Apage%3Aemail_email_job_alert_digest_01%3B%2FqiVQpxoRkSa9DgLVSm7EQ%3D%3D&midToken=AQHOmWZkzlO39Q&midSig=3vtYihGNMCFHc1&trk=eml-email_job_alert_digest_01-job_card-0-view_job&trkEmail=eml-email_job_alert_digest_01-job_card-0-view_job-null-2l9y4~luykrlt2~t-null-null&eid=2l9y4-luykrlt2-t&otpToken=MTYwNjFiZTExYjJlYzljZWI1MjkwNGU5NDYxYWU2YjI4N2M4ZDA0NDllYTQ4YjZkNzljMzA1NmU0ZjU5NWRmOWYyZDA4NGJlNGZjN2MxZTc0NzQ3MmI3Yzk1N2FlOGQxMjUyYzY2NTYzMDA0YmI1YSwxLDE%3D""", """
Your job alert for head of engineering in Boulder
13 new jobs match your preferences.
Vice President of Engineering
Signify Technology
United States
This company is actively hiring
Apply with resume & profile
View job: https://www.linkedin.com/0"""

    bill = """
https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf24871e90dc4ba068c5bb1a2877b649e24bc62abe98408aa746ae3ab31a17cef8fbfcdc55e5bd0e1a257cc1c4ac3b69456f2ad2ffd60bc377b3a 

https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf24871e90dc4ba068c5bb1a2877b649e24bc62abe98408aa746ae3ab31a17cef8fbfcdc55e5bd0e1a257cc1c4ac3b69456f2ad2ffd60bc377b3a 

Dear Keith,
 As requested, this email notification is to let you know that your bill due date is approaching.


The details are below: 

Name on Account:KEITH NORDSTROM
Xcel Energy Account Number:XX-2776579-X
Bill Statement Date:April 01, 2024
Statement Balance:$172.91
Due Date:April 19, 2024



 Keep in mind, the statement balance might not be due if you've already made a payment or if you have a zero balance. If your payment has been made, sent or is already scheduled, thank you.

To update your notifications, please sign into
https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf2485949d2dad98d189c043fd49511c0e93d08ced08c8d8cdf5d306696e6e99ae89be7c85e8f45546a536614facacabc72932a46d460602ecb27 
My Account. You can also access detailed information about your bill and your energy usage. Not yet enrolled? 
https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf2485949d2dad98d189c043fd49511c0e93d08ced08c8d8cdf5d306696e6e99ae89be7c85e8f45546a536614facacabc72932a46d460602ecb27 
Sign up today.

 
https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf248a36eec28c9a6a4171bf6dda0f255571cfbb635e86a4a2ca01f372a64fd66f4e15819cbbce3b03413d35770530db9f697bbfde2c657ae03fb 
     Pay Now     

   

 Sincerely,

Xcel Energy Customer Care

   


 
Understanding Your Energy Bill
 Our bill center helps you understand what's on your bill and explains the costs of your bill. 
https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf248cab15624a93ad5f62e31545ecb05b170c00121a63650f3c59cbe923fd075205f4220755ec352adda93d54f7844eb6f4e0635a151b0113b5f 
Learn about your bill.




 
Need Help Paying Your Bill? 
Paying your bill shouldn't have to be difficult. We have a variety of 
https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf248986f1205f21cc7c675066af859c548ef52de31bd9b9e68b5bcff3519ee6d4b9893c05134108373e0ae31a02cc3cf037baa8abfd4b5c4cca9 
resources and payment options available . We can help.




Download the App Today
https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf248a8c755744e4e7d12c55c36f5cda28427c7aafca49cb6b125d6e844ffa262b31bb118de90e1955691258a0687e0506d45ef27683c1213f5ba 

https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf2487d6cb9dd2ea0d270ab6be9053cbb2db6f0b79e923572ae6d38571068d4ceea59ad77ee972ad6663044aebb5b88f2f7ae537ad7beb142b9a1 


 
 
 
 

https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf248a36eec28c9a6a4171bf6dda0f255571cfbb635e86a4a2ca01f372a64fd66f4e15819cbbce3b03413d35770530db9f697bbfde2c657ae03fb 
Pay Bill 
https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf2480d831f0466b2894baf1d20cafc098d56ee6aaf468ae750c68f7b5a5e6808f558e985a497c7b61f3ecc40ca10da903ab21a1f0ee973a754b4 
Programs & Rebates 

https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf2482a52f6af246cf5d66690a9bfb1a28bdc7fd33c1425e340112ef996bfbf0fc67fa43d36b694a9c7c57ccc71d3cf1dfdbd9f92b7f735dae022 
Start/Stop Service 
https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf248593b7a4dc6b546f29148d30077b1203c9ff35201fe2566a9a241776243e5ef13c55f3fc504cabf9e6a4d62b07b6acb413291f1f616c2b51d 
Outages 

https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf2485949d2dad98d189c043fd49511c0e93d08ced08c8d8cdf5d306696e6e99ae89be7c85e8f45546a536614facacabc72932a46d460602ecb27 
My Account 
https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf248a3a37787d0425c2ee4f6288eb1fcd0a60e5320d8e127aa6d5d2346fd7ece081352e892a90bd69fcba351c612255bdc6068c522495dc344d9 
Customer Support 

https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf2485949d2dad98d189c043fd49511c0e93d08ced08c8d8cdf5d306696e6e99ae89be7c85e8f45546a536614facacabc72932a46d460602ecb27 
My Account 
https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf248a3a37787d0425c2ee4f6288eb1fcd0a60e5320d8e127aa6d5d2346fd7ece081352e892a90bd69fcba351c612255bdc6068c522495dc344d9 
Customer Support 
https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf2489de22fde0df25a4de3826fcf7d5336e1be49f04aa6c5f4b1c49c35292859e0284b1eb42c18c933c226fbdf40ebf86d801e02a289db0dbc24 
Privacy Policy 


 You are receiving this email because you opted to receive information from Xcel Energy.

 Please add 
mailto:email@energyco.com 
email@energyco.com to your sender list. 
Google Play and the Google Play logo are trademarks of Google LLC.

App Store and Apple logo are registered trademarks of Apple Inc. 
 

https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf248a21b4ebb4d0d2dbd476afbbac9e2aeeb24171a28d55d990873aa3e1cb7303ec449ca64ca12b5a7b199b641c1d7aa4a30ff1659d5d2fa7a1d 

https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf24813eb5916a8f809e13cd6ab9d2341b0a96d33965b4ea08b61462934a4c212625c3ec3d07003ff6f0c82a8986deb2d229bceea41e7a50c8b59 

https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf2480dc985585d6f7eee26ae1dc3c76102355e1e5fcf948bac1965ff2bc660185e689c8c5872618d77ed91f501a8bb3e86314239ca19c6b4dc5b 

https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf2487b7fc519492d2159f7247f95ba10f466481fa87764afd91d3ee533e2c20478764ba7ce20ff6dc15009bb1b2470a9627c51f99a8535f92d0c 

https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf248d8fab3ef85629f6afad6944ca4a64d91099e56b19f8e6df72ef0020658dd91ae1f956343ce8af4f77e9f9001bcca0a8ef50785b3c64aa884 

https://click.marketing.xcelenergy.com/?qs=ca7315dfe9ecf248c7dee0a7f0d05b4203a6e1877326cc7bb9402cbfd321a0f3c2f183e3363d20e0f381e2af273f7147543c5691549ca8ebba57b9687d02a42d 
Our Blog 


 (c) 2024 XCEL ENERGY INC. ALL RIGHTS RESERVED. 

 414 NICOLLET MALL, MINNEAPOLIS, MN 55401""", """
https://click.marketing.xcelenergy.com/0 
https://click.marketing.xcelenergy.com/0 
Dear Keith,
 As requested, this email notification is to let you know that your bill due date is approaching.
The details are below: 
Name on Account:KEITH NORDSTROM
Xcel Energy Account Number:XX-2776579-X
Bill Statement Date:April 01, 2024
Statement Balance:$172.91
Due Date:April 19, 2024
 Keep in mind, the statement balance might not be due if you've already made a payment or if you have a zero balance. If your payment has been made, sent or is already scheduled, thank you.
To update your notifications, please sign into
https://click.marketing.xcelenergy.com/2 
My Account. You can also access detailed information about your bill and your energy usage. Not yet enrolled? 
https://click.marketing.xcelenergy.com/2 
Sign up today.
 
https://click.marketing.xcelenergy.com/4 
     Pay Now     
   
 Sincerely,
Xcel Energy Customer Care
   
 
Understanding Your Energy Bill
 Our bill center helps you understand what's on your bill and explains the costs of your bill. 
https://click.marketing.xcelenergy.com/5 
Learn about your bill.
 
Need Help Paying Your Bill? 
Paying your bill shouldn't have to be difficult. We have a variety of 
https://click.marketing.xcelenergy.com/6 
resources and payment options available . We can help.
Download the App Today
https://click.marketing.xcelenergy.com/7 
https://click.marketing.xcelenergy.com/8 
 
 
 
 
https://click.marketing.xcelenergy.com/4 
Pay Bill 
https://click.marketing.xcelenergy.com/10 
Programs & Rebates 
https://click.marketing.xcelenergy.com/11 
Start/Stop Service 
https://click.marketing.xcelenergy.com/12 
Outages 
https://click.marketing.xcelenergy.com/2 
My Account 
https://click.marketing.xcelenergy.com/14 
Customer Support 
https://click.marketing.xcelenergy.com/2 
My Account 
https://click.marketing.xcelenergy.com/14 
Customer Support 
https://click.marketing.xcelenergy.com/17 
Privacy Policy 
 You are receiving this email because you opted to receive information from Xcel Energy.
 Please add 
mailto:email@energyco.com 
email@energyco.com to your sender list. 
Google Play and the Google Play logo are trademarks of Google LLC.
App Store and Apple logo are registered trademarks of Apple Inc. 
 
https://click.marketing.xcelenergy.com/18 
https://click.marketing.xcelenergy.com/19 
https://click.marketing.xcelenergy.com/20 
https://click.marketing.xcelenergy.com/21 
https://click.marketing.xcelenergy.com/22 
https://click.marketing.xcelenergy.com/23 
Our Blog 
 (c) 2024 XCEL ENERGY INC. ALL RIGHTS RESERVED. 
 414 NICOLLET MALL, MINNEAPOLIS, MN 55401"""
    
    general = """Hi all - I'm hiring senior and lead engineers -

Full details here - https://www.stride.build/careers

NYC and Chicago are ideal yet we are open to hiring anywhere within the
US.

If you know anyone, please have them email me directly so I know they came
through this group - person@stride.build

Thanks!""","""Hi all - I'm hiring senior and lead engineers -
Full details here - https://www.stride.build/0
NYC and Chicago are ideal yet we are open to hiring anywhere within the
US.
If you know anyone, please have them email me directly so I know they came
through this group - person@stride.build
Thanks!"""