import re
from enum import Enum


class Review_Type(Enum):
    ONE_STAR = 1,
    TWO_STAR = 2,
    THREE_STAR = 3,
    FOUR_STAR = 4,
    FIVE_STAR = 5


class URL_Processor():

    IBSN = None
    URL = None
    Review_Type = None
    Page_Number = 1
    Review_URL = None

    def __init__(self, URL, Review_Type=Review_Type, Page_Number=1):
        self.URL = URL
        self.Review_Type = Review_Type
        self.Page_Number = Page_Number

    def Extract_ISBN(self):
        """
        For any Amazon URL, there will be a pattern: /dp/ or /gp/product/ followed by a 10 or 13 digit ISBN number.
        Extract ISBN number from the URL is sufficient to get to any product details.
        """
        pattern = r'(?:(\/dp\/)|(\/gp\/product\/))([A-Z0-9]{10,13})(?![A-Z0-9])'
        match = re.search(pattern, self.URL)
        if match:
            self.IBSN = match.group(3)
            return self.IBSN
        else:
            raise ValueError("Invalid URL. No ISBN number found.")

    def Compose_Review_URL(self):
        """
        Only take the verified reviews from Amazon.
        Starting with Page 1 and 5 star reviews.

        3 parts of the URL:
        1. Base URL: https://www.amazon.com/product-reviews/
        2. ISBN: B00P00QPPY
        3. URL Parameters: 
                        ie=UTF8
                        reviewerType=avp_only_reviews
                        filterByStar=five_star
        """
        base_url = f"https://www.amazon.com/product-reviews/{self.IBSN}/ref=cm_cr_arp_d_paging_btm_next_{self.Page_Number}?ie=UTF8&reviewerType=avp_only_reviews"
        Review_Type = f"filterByStar={self.Review_Type.name.lower()}"
        Page_Number = f"pageNumber={self.Page_Number}"
        self.Review_URL = f"{base_url}&{Review_Type}&{Page_Number}"
        return self.Review_URL


links = [
    "https://www.amazon.com/Nike-Womens-Running-Metallic-Numeric_12/dp/B01AMT0EYU/ref=cm_cr_arp_d_product_top?ie=UTF8",
    "https://www.amazon.com/gp/product/B007B9NXAC/ref=ppx_yo_dt_b_asin_title_o01_s00?ie=UTF8&psc=1",
    "https://www.amazon.com/gp/product/B09XQVB4XC/ref=ppx_yo_dt_b_asin_title_o03_s00?ie=UTF8&psc=1",
    "https://www.amazon.com/Skytech-Gaming-Nebula-PC-Desktop/dp/B0C9PNZJCF/ref=cm_cr_arp_d_product_top?ie=UTF8",
    "https://www.amazon.com/PNY-CS900-500GB-Internal-Solid/dp/B07XZLN9KM/ref=pd_gw_ssd_gw_btf_ee_t2_c_9?_encoding=UTF8&dd=PwlnOuZJs7-VlkGqH4n5MNNGzeC2M1AGI-JCm90QnS4%2C&ddc_refnmnt=free&pd_rd_i=B07XZLN9KM&pd_rd_w=j17gH&content-id=amzn1.sym.c2ae9050-5982-4dae-9854-9fb90fe645ed&pf_rd_p=c2ae9050-5982-4dae-9854-9fb90fe645ed&pf_rd_r=NAHS725ZF9W4JN8Y4CMB&pd_rd_wg=lXFQT&pd_rd_r=551fd574-d62d-4cbe-831b-b5b9106b5777&th=1",
    "https://www.amazon.com/Kingston-240GB-Solid-SA400S37-240G/dp/B01N5IB20Q/ref=sr_1_4?crid=RBCSBVTE7RE6&dib=eyJ2IjoiMSJ9.xeUlNirdrkmaHaA9lR1ZwfcNsPHiAaHVLXWsRNSuyrXWUM_yY5LyFAFqoCxOv3T6aC1VK0-ePDtKe8l9YH5EbV1pfzyK2gDwGPWpsSridZAZ_GcsszuGyP-XDbJMALlTsAXZwxrMw06qulyetsJIdFt1l1d924uFJ93sey5xUUKAC6HEAH92i9qoEwXkMIZI6rkpNsqie-RhMDRvN_I82rzeFkZcUgAAImoAq-JgeQg.S4yqGaTf222GH2HY2kdqFmJbzi6u3UfmZgHB0JMegWU&dib_tag=se&keywords=ssd&qid=1712175261&sprefix=s%2Caps%2C522&sr=8-4",
    "https://www.amazon.com/SAMSUNG-Inch-Internal-MZ-77E2T0B-AM/dp/B08QB93S6R/ref=sr_1_3?crid=RBCSBVTE7RE6&dib=eyJ2IjoiMSJ9.xeUlNirdrkmaHaA9lR1ZwfcNsPHiAaHVLXWsRNSuyrXWUM_yY5LyFAFqoCxOv3T6aC1VK0-ePDtKe8l9YH5EbV1pfzyK2gDwGPWpsSridZAZ_GcsszuGyP-XDbJMALlTsAXZwxrMw06qulyetsJIdFt1l1d924uFJ93sey5xUUKAC6HEAH92i9qoEwXkMIZI6rkpNsqie-RhMDRvN_I82rzeFkZcUgAAImoAq-JgeQg.S4yqGaTf222GH2HY2kdqFmJbzi6u3UfmZgHB0JMegWU&dib_tag=se&keywords=ssd&qid=1712175261&sprefix=s%2Caps%2C522&sr=8-3&th=1",
    "https://www.amazon.com/Band-Aid-Flexible-Fabric-Adhesive-Bandages/dp/B00006IDL6/ref=pd_gw_ssd_gw_btf_ts_t3_c_5?_encoding=UTF8&dd=PwlnOuZJs7-VlkGqH4n5MNNGzeC2M1AGI-JCm90QnS4%2C&ddc_refnmnt=free&pd_rd_i=B00006IDL6&pd_rd_w=XzlhZ&content-id=amzn1.sym.d89f3fe7-9df8-401e-b51d-e272f6577f92&pf_rd_p=d89f3fe7-9df8-401e-b51d-e272f6577f92&pf_rd_r=DJGAYR7AZACZ8VVKDDGX&pd_rd_wg=exkHG&pd_rd_r=deefeae5-8177-4fd1-a03b-7b96b48d2da8",
    "https://www.amazon.com/Colgate-Advanced-Whitening-Toothpaste-Sparkling/dp/B082F1QH7S/ref=pd_gw_ssd_gw_btf_ts_t3_c_6?_encoding=UTF8&dd=PwlnOuZJs7-VlkGqH4n5MNNGzeC2M1AGI-JCm90QnS4%2C&ddc_refnmnt=free&pd_rd_i=B082F1QH7S&pd_rd_w=XzlhZ&content-id=amzn1.sym.d89f3fe7-9df8-401e-b51d-e272f6577f92&pf_rd_p=d89f3fe7-9df8-401e-b51d-e272f6577f92&pf_rd_r=DJGAYR7AZACZ8VVKDDGX&pd_rd_wg=exkHG&pd_rd_r=deefeae5-8177-4fd1-a03b-7b96b48d2da8",
    "https://www.amazon.com/The-Three-Body-Problem-audiobook/dp/B00P00QPPY/ref=sr_1_1?crid=1H3BGG30HSP4Y&dib=eyJ2Ij",
    "https://www.amazon.com/Nike-Womens-Running-Metallic-Numeric_12/dp/B01AMT0EYU/ref=cm_cr_arp_d_product_top?ie=UTF8",
    "https://www.amazon.com/gp/product/B007B9NXAC/ref=ppx_yo_dt_b_asin_title_o01_s00?ie=UTF8&psc=1",
    "https://www.amazon.com/gp/product/B09XQVB4XC/ref=ppx_yo_dt_b_asin_title_o03_s00?ie=UTF8&psc=1",
    "https://www.amazon.com/Skytech-Gaming-Nebula-PC-Desktop/dp/B0C9PNZJCF/ref=cm_cr_arp_d_product_top?ie=UTF8",
    "https://www.amazon.com/PNY-CS900-500GB-Internal-Solid/dp/B07XZLN9KM/ref=pd_gw_ssd_gw_btf_ee_t2_c_9?_encoding=UTF8&dd=PwlnOuZJs7-VlkGqH4n5MNNGzeC2M1AGI-JCm90QnS4%2C&ddc_refnmnt=free&pd_rd_i=B07XZLN9KM&pd_rd_w=j17gH&content-id=amzn1.sym.c2ae9050-5982-4dae-9854-9fb90fe645ed&pf_rd_p=c2ae9050-5982-4dae-9854-9fb90fe645ed&pf_rd_r=NAHS725ZF9W4JN8Y4CMB&pd_rd_wg=lXFQT&pd_rd_r=551fd574-d62d-4cbe-831b-b5b9106b5777&th=1",
    "https://www.amazon.com/Kingston-240GB-Solid-SA400S37-240G/dp/B01N5IB20Q/ref=sr_1_4?crid=RBCSBVTE7RE6&dib=eyJ2IjoiMSJ9.xeUlNirdrkmaHaA9lR1ZwfcNsPHiAaHVLXWsRNSuyrXWUM_yY5LyFAFqoCxOv3T6aC1VK0-ePDtKe8l9YH5EbV1pfzyK2gDwGPWpsSridZAZ_GcsszuGyP-XDbJMALlTsAXZwxrMw06qulyetsJIdFt1l1d924uFJ93sey5xUUKAC6HEAH92i9qoEwXkMIZI6rkpNsqie-RhMDRvN_I82rzeFkZcUgAAImoAq-JgeQg.S4yqGaTf222GH2HY2kdqFmJbzi6u3UfmZgHB0JMegWU&dib_tag=se&keywords=ssd&qid=1712175261&sprefix=s%2Caps%2C522&sr=8-4",
    "https://www.amazon.com/SAMSUNG-Inch-Internal-MZ-77E2T0B-AM/dp/B08QB93S6R/ref=sr_1_3?crid=RBCSBVTE7RE6&dib=eyJ2IjoiMSJ9.xeUlNirdrkmaHaA9lR1ZwfcNsPHiAaHVLXWsRNSuyrXWUM_yY5LyFAFqoCxOv3T6aC1VK0-ePDtKe8l9YH5EbV1pfzyK2gDwGPWpsSridZAZ_GcsszuGyP-XDbJMALlTsAXZwxrMw06qulyetsJIdFt1l1d924uFJ93sey5xUUKAC6HEAH92i9qoEwXkMIZI6rkpNsqie-RhMDRvN_I82rzeFkZcUgAAImoAq-JgeQg.S4yqGaTf222GH2HY2kdqFmJbzi6u3UfmZgHB0JMegWU&dib_tag=se&keywords=ssd&qid=1712175261&sprefix=s%2Caps%2C522&sr=8-3&th=1",
    "https://www.amazon.com/Band-Aid-Flexible-Fabric-Adhesive-Bandages/dp/B00006IDL6/ref=pd_gw_ssd_gw_btf_ts_t3_c_5?_encoding=UTF8&dd=PwlnOuZJs7-VlkGqH4n5MNNGzeC2M1AGI-JCm90QnS4%2C&ddc_refnmnt=free&pd_rd_i=B00006IDL6&pd_rd_w=XzlhZ&content-id=amzn1.sym.d89f3fe7-9df8-401e-b51d-e272f6577f92&pf_rd_p=d89f3fe7-9df8-401e-b51d-e272f6577f92&pf_rd_r=DJGAYR7AZACZ8VVKDDGX&pd_rd_wg=exkHG&pd_rd_r=deefeae5-8177-4fd1-a03b-7b96b48d2da8",
    "https://www.amazon.com/Colgate-Advanced-Whitening-Toothpaste-Sparkling/dp/B082F1QH7S/ref=pd_gw_ssd_gw_btf_ts_t3_c_6?_encoding=UTF8&dd=PwlnOuZJs7-VlkGqH4n5MNNGzeC2M1AGI-JCm90QnS4%2C&ddc_refnmnt=free&pd_rd_i=B082F1QH7S&pd_rd_w=XzlhZ&content-id=amzn1.sym.d89f3fe7-9df8-401e-b51d-e272f6577f92&pf_rd_p=d89f3fe7-9df8-401e-b51d-e272f6577f92&pf_rd_r=DJGAYR7AZACZ8VVKDDGX&pd_rd_wg=exkHG&pd_rd_r=deefeae5-8177-4fd1-a03b-7b96b48d2da8"
]
