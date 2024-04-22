import re


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
        # base_url = f"https://www.amazon.com/product-reviews/{self.IBSN}/ref=cm_cr_getr_d_paging_btm_next_{self.Page_Number}?ie=UTF8&reviewerType=all_reviews"
        # Review_Type = f"filterByStar={self.Review_Type.name.lower()}"
        # Page_Number = f"pageNumber={self.Page_Number}"
        # self.Review_URL = f"{base_url}&{Page_Number}&{Review_Type}"
        # return self.Review_URL
        return f"https://www.amazon.com/product-reviews/{self.IBSN}"
