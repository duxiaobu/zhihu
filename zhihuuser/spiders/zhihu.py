# -*- coding: utf-8 -*-
from scrapy import Spider, Request
import json
from zhihuuser.items import UserItem


class ZhihuSpider(Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    # 关注者列表url
    follow_url = "https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}"
    follow_query = "data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following," \
                  "badge[?(type=best_answerer)].topics"
    # 粉丝列表url
    follower_url = "https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}"
    follower_query = "data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics"

    # 用户详细url
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query = 'locations,employments,gender,educations,business,voteup_count,thanked_Count,follower_count,following_count,cover_url,following_topic_count,following_question_count,following_favlists_count,following_columns_count,answer_count,articles_count,pins_count,question_count,commercial_question_count,favorite_count,favorited_count,logs_count,marked_answers_count,marked_answers_text,message_thread_token,account_status,is_active,is_force_renamed,is_bind_sina,sina_weibo_url,sina_weibo_name,show_sina_weibo,is_blocking,is_blocked,is_following,is_followed,mutual_followees_count,vote_to_count,vote_from_count,thank_to_count,thank_from_count,thanked_count,description,hosted_live_count,participated_live_count,allow_message,industry_category,org_name,org_homepage,badge[?(type=best_answerer)].topics'
    start_user = "excited-vczh"

    def start_requests(self):
        # 关注者列表请求
        yield Request(url=self.follow_url.format(user=self.start_user, include=self.follow_query, offset=0, limit=20), callback=self.parse_follow)
        # 自己详细页面请求
        yield Request(url=self.user_url.format(user=self.start_user, include=self.user_query), callback=self.parse_user)
        # 粉丝列表请求
        yield Request(url=self.follower_url.format(user=self.start_user, include=self.follower_query, offset=0, limit=20), callback=self.parse_follower)

    def parse_user(self, response):
        # 获取单个人的详细列表
        result = json.loads(response.text)
        item = UserItem()
        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)
        yield item
        # 并继续递归的获取这个人的关注列表，爬取这个人关注者的详细信息
        yield Request(url=self.follow_url.format(user=result.get('url_token'), include=self.follow_query, offset=0, limit=20), callback=self.parse_follow)
        #并继续递归的获取这个人的粉丝列表，爬取这个人粉丝的详细信息
        yield Request(url=self.follower_url.format(user=result.get('url_token'), include=self.follower_query, offset=0, limit=20), callback=self.parse_follower)

    def parse_follow(self, response):
        # 解析关注者
        # 把json数据加载成dict
        results = json.loads(response.text)
        if "data" in results.keys():
            for result in results.get('data'):
                yield Request(url=self.user_url.format(user=result.get('url_token'), include=self.user_query), callback=self.parse_user)
        # 判断是否到了最后一页
        if "paging" in results.keys() and results.get('paging').get('is_end') == False:
            next_url = results.get('paging').get('next')
            yield Request(url=next_url, callback=self.parse_follow)

    def parse_follower(self, response):
        # 解析粉丝列表
        results = json.loads(response.text)
        if "data" in results.keys():
            for result in results.get('data'):
                yield Request(url=self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              callback=self.parse_user)
        # 判断是否到了最后一页
        if "paging" in results.keys() and results.get('paging').get('is_end') == False:
            next_url = results.get('paging').get('next')
            yield Request(url=next_url, callback=self.parse_follower)
