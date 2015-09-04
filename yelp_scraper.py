# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import StaleElementReferenceException
import unittest, time, re, sys
import codecs

from selenium.webdriver import ActionChains

class Business:
    def __init__(self, name = '', neighborhood = '',
                    address = '', city = '', state = '',
                    zipcode = '', phone = '', categories = ''):
        self.name = name
        self.neighborhood = neighborhood
        self.address = address
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.phone = phone
        self.categories = categories
        
    def parseFromBizListingLarge(self, bizListingElt, neighborhood=''):
        nameElt = bizListingElt.find_element_by_class_name('biz-name')
        if (nameElt != None):
            self.name = nameElt.text.strip()
            
        try:    
            neighborhoodElt = bizListingElt.find_element_by_class_name('neighborhood-str-list')
            if (neighborhoodElt != None):
                self.neighborhood = neighborhoodElt.text
        except NoSuchElementException:
            # use default neighborhood
            self.neighborhood = neighborhood
            
        addressElt = bizListingElt.find_element_by_tag_name('address')
        if (addressElt != None):
            print(u"addressElt.text: %s" % addressElt.text)
            addressPartList = addressElt.text.split("\n")
            
            if (len(addressPartList) > 1):
                self.address = addressPartList[0].strip()
                cityStateZip = addressPartList[1].strip()
                matchObj = re.match(r'^(.*?),\s+(.*?)\s+(\d+-*\d*)$', cityStateZip)
                if matchObj:
                    self.city = matchObj.group(1)
                    self.state = matchObj.group(2)
                    self.zipcode = matchObj.group(3)
            elif (len(addressPartList) == 1):
                cityStateZip = addressPartList[0].strip()
                matchObj = re.match(r'^(.*?),\s+(.*?)\s+(\d+-*\d*)$', cityStateZip)
                if matchObj:
                    self.city = matchObj.group(1)
                    self.state = matchObj.group(2)
                    self.zipcode = matchObj.group(3)
             
        phoneElt = bizListingElt.find_element_by_class_name('biz-phone')
        if (phoneElt != None):
            self.phone = phoneElt.text.strip()
            
        categoryListElt = bizListingElt.find_element_by_class_name('category-str-list')
        if (categoryListElt != None):
            categoriesElt = categoryListElt.find_elements_by_tag_name('a')
            if (categoriesElt != None and len(categoriesElt) > 0):
                self.categories = []
                for categoryElt in categoriesElt:
                    self.categories.append(categoryElt.text.strip())
                    
        return self
  
    def getCategoriesStr(self):
        if (self.categories != None and len(self.categories) > 0):
            categoriesStr = self.categories[0]
            for i in range(2,len(self.categories)):
                categoriesStr += u", " + self.categories[i]
        else:
            categoriesStr = None
            
        return categoriesStr
  
    def __str__(self):
        categoriesStr = self.getCategoriesStr().encode("ascii", "ignore")
            
        return ("[name = %s, neighborhood = %s, address = %s, city = %s, state = %s, zipcode = %s, phone = %s, categories = {%s}]" % 
                    (self.name, self.neighborhood, self.address, self.city, self.state, self.zipcode, self.phone, categoriesStr))
        
    def toPipeDelimitedUnicode(self):
        categoriesStr = self.getCategoriesStr()
        
        return ("%s|%s|%s|%s|%s|%s|%s|%s" % 
                    (self.name, self.neighborhood, self.address, self.city, self.state, self.zipcode, self.phone, categoriesStr))        

class YelpScraper(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.defaultWaitTime = 15
        self.driver.implicitly_wait(self.defaultWaitTime)
        self.base_url = "http://www.yelp.com/"
        self.verificationErrors = []
        self.accept_next_alert = True
        self.businessList = []
        
        self.sf_neighborhoods = [
                    'Alamo Square', 
                    'Anza Vista', 
                    'Ashbury Heights', 
                    'Balboa Terrace', 
                    'Bayview-Hunters Point', 
                    'Bernal Heights', 
                    'Castro', 
                    'Chinatown', 
                    'Civic Center', 
                    'Cole Valley', 
                    'Corona Heights', 
                    'Crocker-Amazon', 
                    'Diamond Heights', 
                    'Dogpatch', 
                    'Duboce Triangle', 
                    'Embarcadero', 
                    'Excelsior', 
                    'Fillmore', 
                    'Financial District', 
                    "Fisherman's Wharf", 
                    'Forest Hill', 
                    'Glen Park', 
                    'Hayes Valley', 
                    'Ingleside', 
                    'Ingleside Heights', 
                    'Ingleside Terraces', 
                    'Inner Richmond', 
                    'Inner Sunset', 
                    'Japantown', 
                    'Lakeshore', 
                    'Lakeside', 
                    'Laurel Heights', 
                    'Lower Haight', 
                    'Lower Nob Hill', 
                    'Lower Pacific Heights', 
                    'Marina/Cow Hollow', 
                    'Merced Heights', 
                    'Merced Manor', 
                    'Miraloma Park', 
                    'Mission', 
                    'Mission Bay', 
                    'Mission Terrace', 
                    'Monterey Heights', 
                    'Mount Davidson Manor', 
                    'NoPa', 
                    'Nob Hill', 
                    'Noe Valley', 
                    'North Beach/Telegraph Hill', 
                    'Oceanview', 
                    'Outer Mission', 
                    'Outer Richmond', 
                    'Outer Sunset', 
                    'Pacific Heights', 
                    'Parkmerced', 
                    'Parkside', 
                    'Portola', 
                    'Potrero Hill', 
                    'Presidio', 
                    'Presidio Heights', 
                    'Russian Hill', 
                    'Sea Cliff', 
                    'Sherwood Forest', 
                    'SoMa', 
                    'South Beach', 
                    'St Francis Wood', 
                    'Stonestown', 
                    'Sunnyside', 
                    'Tenderloin', 
                    'The Haight', 
                    'Twin Peaks', 
                    'Union Square', 
                    'Visitacion Valley', 
                    'West Portal', 
                    'Western Addition', 
                    'Westwood Highlands', 
            'Westwood Park']
        
    def scrollAndClickElt(self, findByFnc, findVal):
        self.driver.implicitly_wait(15)
        scale = 0.0
        eltFound = False
        while(scale <= 1.0 and not eltFound):
            #print("trying to find link at %f" % scale)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight*%s);" % scale)
            
            elt = findByFnc(findVal)
            if (elt != None):
                try:
                    elt.click()
                    #print("elt found")
                    eltFound = True
                except StaleElementReferenceException:
                    print("moving down")
                    scale += 0.1
            else:
                #print("moving down")
                scale += 0.1
                
        if (not eltFound):
            raise Exception("elt not found")
            
        self.driver.implicitly_wait(self.defaultWaitTime)
        
    def uncheckPlaceCheckboxes(self):
        for neighborhood in self.sf_neighborhoods:
            value="//div[@class=\"ypop-content clearfix ytype\"]//input[@value=\"CA:San_Francisco::%s\"]" % neighborhood.replace (" ", "_")
            #print(value)
           
            checkbox = self.driver.find_element_by_xpath(value)
            if (checkbox.is_selected()):
                checkbox.click()
                
    def findLinkFromListByText(self, links, text):
        if (links == None or len(links) == 0):
            #print("(links == None or len(links) == 0)")
            return None
            
        for link in links:
            try:
                #print("findLinkFromListByText: %s" % link.text.strip())
            
                if (link.text.strip() == text):
                    return True
            except UnicodeEncodeError:
                # fuck python and how it handles unicode. so ass backward.
                print("skip unicode link (probably ->)")
                
        return None
        
    def traversePlace(self, neighborhood):
        self.getBizListing(neighborhood)
    
        links = self.driver.find_elements_by_xpath("//ul[@class='pagination-links arrange_unit arrange_unit--stack-12']//li/a")
        currPage = 1
        doneFlag = False
        while (not doneFlag):
            currPage += 1
            #print("currPage: %d" % currPage)
            currPageStr = str(currPage)
            link = self.findLinkFromListByText(links, currPageStr)
            if (link != None):
                self.getBizListing(neighborhood)
            else:
                doneFlag = True    
                
    def getBizListing(self, neighborhood):
        bizListingEltList = self.driver.find_elements_by_class_name("biz-listing-large")
        if (bizListingEltList != None and len(bizListingEltList) > 0):
            for bizListingElt in bizListingEltList:
                business = Business().parseFromBizListingLarge(bizListingElt, neighborhood)
                self.businessList.append(business)
                print(business.__str__().encode("ascii", "ignore"))
                
    def writeToUnicodeFile(self, filename):
        f = codecs.open(filename, encoding='utf-8', mode='w')

        if (self.businessList != None and len(self.businessList) > 0):
            for business in self.businessList:
                f.write(business.toPipeDelimitedUnicode() + "\n")

        f.close()
                      
    def test_yelp_scraper(self):
        sleepTime = 5
        driver = self.driver
        driver.maximize_window()
        
        driver.get(self.base_url + "/")
        driver.find_element_by_id("dropperText_Mast").clear()
        driver.find_element_by_id("dropperText_Mast").send_keys("san francisco, ca")
        driver.find_element_by_id("header-search-submit").click()
        #driver.find_element_by_link_text("Restaurants").click()
        #driver.find_element_by_link_text("Bars").click()
        driver.find_element_by_link_text("Coffee & Tea").click()
        
        time.sleep( sleepTime )
        
        for neighborhood in self.sf_neighborhoods:
        #neighborhoods = self.sf_neighborhoods[5:6]
        #for neighborhood in neighborhoods:
            print(neighborhood)
            self.scrollAndClickElt(driver.find_element_by_link_text, "More Neighborhoods")
            time.sleep( sleepTime )
            self.uncheckPlaceCheckboxes()
            value="//div[@class=\"ypop-content clearfix ytype\"]//input[@value=\"CA:San_Francisco::%s\"]" % neighborhood.replace (" ", "_")
            self.scrollAndClickElt(driver.find_element_by_xpath, value)
            self.scrollAndClickElt(driver.find_element_by_xpath, "(//button[@value='submit'])[6]")
            time.sleep( sleepTime )
            
            self.traversePlace(neighborhood)        
            
        #self.writeToUnicodeFile('restaurants.txt')  
        #self.writeToUnicodeFile('bars.txt')  
        self.writeToUnicodeFile('coffeetea.txt')  
    
    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException, e: return False
        return True
    
    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True
    
    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
