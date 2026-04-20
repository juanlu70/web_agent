(function() { function bxBootstrap() {
	var re = /bot|crawl|slurp|spider|mediapartners|headlesschrome|snap-prefetch|remotasks|woorank|uptime\.com|facebookexternalhit|facebookcatalog/i;
	if (re.test(navigator.userAgent) || navigator.userAgent == '') {
		return;
	}

	if (!(window.bouncex&&bouncex.website)) {
		var pushedData = [];
		var pushedClientEvents = [];
		if(window.bouncex && bouncex.push && bouncex.length){
			pushedData = bouncex;
		}
		if (window.bouncex && bouncex.clientEvents && bouncex.clientEvents.length) {
           pushedClientEvents = bouncex.clientEvents;
        }
		window.bouncex = {};
		bouncex.pushedData = pushedData;
		bouncex.pushedClientEvents = pushedClientEvents;
		bouncex.website = {"id":6384,"name":"Vox Media | The Verge","cookie_name":"bounceClientVisit6384","domain":"theverge.com","ct":"bind_to_domain","ally":0,"ei":0,"tcjs":"","cjs":"/* enable.feature.UID2 */","force_https":false,"waypoints":false,"content_width":900,"gai":"","swids":"","sd":0,"ljq":"auto","campaign_id":0,"is_preview":false,"aco":{"first_party_limit":"3500","local_storage":"1"},"cmp":{"gdpr":1,"gmp":0,"whitelist_check":0},"burls":[],"ple":false,"fbe":true,"ffs":"","mas":2,"map":1,"gar":true,"ete":2,"ettm":true,"etjs":"","dge":true,"bxidLoadFirst":false,"pie":true,"cme":true,"gbi_enabled":1,"bpush":false,"pt":{"article":{"testmode":false,"val":[[{"activation":"js","prop":"","prop2":"","prop3":"","val":"document.querySelectorAll('.duet--article--lede, .duet--page-layout--standard-article').length > 0;"}],[{"activation":"js","prop":"","prop2":"","prop3":"","val":"document.querySelectorAll('.duet--media--video-embed').length === 0;"}],[{"activation":"js","prop":"","prop2":"","prop3":"","val":"document.querySelectorAll('[aria-describedby=\"tooltip-Podcasts\"]').length === 0;"}]]},"author":{"testmode":false,"val":[[{"activation":"js","prop":"","prop2":"","prop3":"","val":" document.querySelectorAll('.duet--page-layout--author').length > 0;"}]]},"category":{"testmode":false,"val":[[{"activation":"js","prop":"","prop2":"","prop3":"","val":" document.querySelectorAll('.duet--page-layout--category').length > 0;"}]]},"home":{"testmode":false,"val":[[{"activation":"js","prop":"","prop2":"","prop3":"","val":"document.querySelectorAll('.duet--page-layout--homepage').length > 0"},{"activation":"js","prop":"","prop2":"","prop3":"","val":"window.location.pathname === '/'"}]]},"podcast":{"testmode":false,"val":[[{"activation":"js","prop":"","prop2":"","prop3":"","val":"document.querySelectorAll('[aria-describedby=\"tooltip-Podcasts\"]').length > 0;"}]]},"video":{"testmode":false,"val":[[{"activation":"js","prop":"","prop2":"","prop3":"","val":"document.querySelectorAll('.duet--media--video-embed').length>0;"}]]}},"els":{},"vars":[{"name":"dfp_rblock","polling":"all","persist":"visit","page_types":[],"testmode":true,"default":"false","code":"/* dfp_rblock */\n(function() {\n    if (!bouncex.dfpRan) {\n        bouncex.dfpRan = true;\n        return 'not_ready';\n    }\n    function check() {\n        bouncex.dfp_loaded = false || bouncex.dfp_loaded;\n        \n        var event = bouncex.gbi2.getDfpEndPageViewEvent();\n        \n        if (event && event.dfp_status) {\n            if (event.dfp_status == 'pending') {\n                return 'not_ready';\n            } \n            \n            bouncex.dfp_loaded = true;\n\n            if (event.dfp_status == 'suppressed') {\n                bouncex.log('sponsor!!!!!');\n                return 'sponsor';\n            }\n            bouncex.log('allow!!!!!');\n            return 'allow';\n        }\n\n        return 'not_ready';\n    }\n\n    if (bouncex.website.gbi.rblocks) {\n        if (bouncex.dfp_loaded) {\n            return null;\n        } else if (window.googletag && googletag.apiReady && googletag.pubadsReady && bouncex.gbi2) {\n            bouncex.log('checking!!!');\n            return check();\n        } else if (typeof window.googletag === 'undefined') {\n            return 'no_googletag';\n        }\n        return 'fallback';\n    } else {\n        return 'not_ready';\n    }\n})();\n","trigger":"pageload"},{"name":"page_type","polling":"none","persist":"no","page_types":[],"testmode":false,"default":"false","code":"bouncex.website.pts;","trigger":"pageload"},{"name":"page_category_tag","polling":"all","persist":"no","page_types":[],"testmode":false,"default":"false","code":"(() => {\n    if (bouncex.website.pts === 'category') {\n        return jQuery(h1).first().text();\n    }\n    \n\tconst categoriesToTrack = {\n\t\t'buying-guides': 'Buying Guides',\n\t\t'news': 'News',\n\t\t'good-deals': 'Deals'\n\t};\n\n\tconst dataLayerArticleData = window.dataLayer.filter(item => item['Primary Category'] || item['Categories']);\n\n\tif (!dataLayerArticleData.length) {\n\t\treturn 'Unknown'; // could maybe also try to scrape from the DOM, but not a super reliable class or ID to use\n\t}\n\n\tconst primaryCategory = dataLayerArticleData[0]['Primary Category'];\n\n\t// pull primary category if matches\n\tif (categoriesToTrack[primaryCategory]) {\n\t\treturn categoriesToTrack[primaryCategory];\n\t}\n\n\t// primary category doesn't match, let's look in all categories\n\tconst articleCategories = dataLayerArticleData[0]['Categories'];\n\n\tif (articleCategories) {\n\t\tfor (const category of Object.keys(categoriesToTrack)) {\n\t\t\tif (articleCategories.split(',').includes(category)) {\n\t\t\t\treturn categoriesToTrack[category];\n\t\t\t}\n\t\t}\n\t}\n\n\treturn primaryCategory || 'Unknown';\n})();","trigger":"pageload"},{"name":"logged_in","polling":"all","persist":"no","page_types":[],"testmode":false,"default":"false","code":"(function() {\n  var match = jQuery(\"span._6cuzo23\").filter(function() {\n    return jQuery(this).text().trim().toLowerCase() === \"account\";\n  });\n\n  if (match.length > 0) {\n    return true;\n  }\n})();","trigger":"pageload"},{"name":"subscriber_conversion_status","polling":"all","persist":"no","page_types":[],"testmode":false,"default":"false","code":"jQuery('._6cuzo21').length === 0 && bouncex.vars.logged_in;","trigger":"pageload"},{"name":"submitted_email_list_verge_deals","polling":"none","persist":"permanent","page_types":[],"testmode":false,"default":"false","code":"null;","trigger":"pageload"},{"name":"submitted_email_list_verge_daily","polling":"none","persist":"permanent","page_types":[],"testmode":false,"default":"false","code":"null;","trigger":"pageload"},{"name":"ever_logged_in","polling":"all","persist":"permanent","page_types":[],"testmode":false,"default":"false","code":"bouncex.vars.logged_in || null;","trigger":"pageload"},{"name":"submitted_onsite","polling":"all","persist":"permanent","page_types":[],"testmode":false,"default":"false","code":"jQuery('.a18g6gv.a18g6gs.a18g6gx').text().trim().indexOf('Success') > -1 || jQuery('.duet--article--article-body-component .duet--cta--newsletter').text().trim().indexOf('Thanks for signing up') > -1 || null","trigger":"pageload"},{"name":"paywall_present","polling":"vars","persist":"no","page_types":[],"testmode":false,"default":"false","code":"jQuery('#zephr-footer-container').is(':visible');","trigger":"pageload"},{"name":"ad_blocker_present","polling":"all","persist":"no","page_types":[],"testmode":false,"default":"false","code":"jQuery(\"._9r0K-Oum._5kE-6aUK:contains('Support The Verge by allowing ads')\").is(':visible') || jQuery('.bj5ZM4fy').is(':visible');","trigger":"pageload"},{"name":"registered_user_free_article","polling":"none","persist":"no","page_types":[],"testmode":false,"default":"false","code":"(dataLayer||[]).some(dl=>((dl[\"All Categories\"]||[]).toString().split(',').map(v=>v.trim()).includes(\"free-to-read\")));","trigger":"pageload"}],"dgu":"pixel.cdnwidget.com","dgp":false,"ba":{"enabled":0,"fbte":0},"biu":"assets.bounceexchange.com","bau":"api.bounceexchange.com","beu":"events.bouncex.net","ibx":{"tjs":"","cjs":"","miw":0,"mibcx":1,"te":1,"cart_rep":{"get":"","set":""},"ulpj":{"bxid":"espemailid"},"cus":"","miw_exclude":"","enabled":1},"etjson":null,"osre":true,"osru":"osr.bounceexchange.com/v1/osr/items","checkDfp":false,"gamNetwork":"","spa":0,"spatm":1,"preinit_cjs":"","crs":{"integrations":null,"pageCount":null},"mat":0,"math":0,"cpnu":"coupons.bounceexchange.com","dfpcms":0,"sms":{"optm":"","eventSharing":false,"shqId":"","enabled":0},"pde":true,"fmc":["AW","AI","AG","AR","BS","BB","BZ","BM","BO","BQ","BR","CA","KY","CL","CO","CR","CU","CW","DM","DO","EC","SV","GF","GL","GD","GT","GP","HT","HN","JM","MQ","MX","MS","NI","PA","PY","PE","PR","PM","MF","BL","KN","LC","VC","SX","SR","TT","US","UM","UY","VE","VG","VI"],"fme":true,"fmx":"","uid2":true,"iiq":false,"sdk":{"android":{"enabled":false,"enabledVersions":[],"eventModifications":null},"ios":{"enabled":false,"enabledVersions":[],"eventModifications":null}},"onsite":{"enabled":1},"ads":{"enabled":1},"pubs":{"enabled":1},"websdk":{"enabled":0,"devMode":0},"ga4_property_id":"","ga4_measurement_id":"","tag_state_domain":"","tag_state_domain_enabled":false,"tag_state_sst_enabled":false}
;

		bouncex.tag = 'tag3';
		bouncex.$ = window.jQuery;
		bouncex.env = 'production';
		bouncex.restrictedTlds = {"casl":{"ca":1},"gdpr":{"ad":1,"al":1,"at":1,"ax":1,"ba":1,"be":1,"bg":1,"by":1,"xn--90ais":1,"ch":1,"cy":1,"cz":1,"de":1,"dk":1,"ee":1,"es":1,"eu":1,"fi":1,"fo":1,"fr":1,"uk":1,"gb":1,"gg":1,"gi":1,"gr":1,"hr":1,"hu":1,"ie":1,"im":1,"is":1,"it":1,"je":1,"li":1,"lt":1,"lu":1,"lv":1,"mc":1,"md":1,"me":1,"mk":1,"xn--d1al":1,"mt":1,"nl":1,"no":1,"pl":1,"pt":1,"ro":1,"rs":1,"xn--90a3ac":1,"ru":1,"su":1,"xn--p1ai":1,"se":1,"si":1,"sj":1,"sk":1,"sm":1,"ua":1,"xn--j1amh":1,"va":1,"tr":1}};
		bouncex.client = {
			supportsBrotli: 1
		};
		bouncex.assets = {"ads":"fdaa8d77359124608f52c18d19ca2db6","creativesBaseStyles":"a53944a2","gpsAuction":"bbb80866120d17013073bb6d284cbd6b","inbox":"d6c8d32b386d0fba348241d2c8b6dbc7","onsite":"1238d00d70e4de87443df9eb69ff1a61","sms":"e39203556bab2366e56296ce42e974a7","websdk":"04a8259886e8489210ad79167d61255e","website_campaigns_6384":"3e7839b2f1b06660a1108a894c0fea8b"};
		bouncex.push = function(pushData) {
			bouncex.pushedData.push(pushData);
		}

		var runtime = document.createElement('script');
		runtime.setAttribute('src', '//assets.bounceexchange.com/assets/smart-tag/versioned/runtime_c81e76ee00d795b1eebf8d27949f8dc5.br.js');
		runtime.setAttribute('async', 'async');

		bouncex.initializeTag = function() {
			var script = document.createElement('script');
			script.setAttribute('src', '//assets.bounceexchange.com/assets/smart-tag/versioned/main-v2_a8ec0b4e51efd1e1ddbdf1b4c6576803.br.js');
			script.setAttribute('async', 'async');
			document.body.appendChild(script);


			var deviceGraphScript = document.createElement('script');
			deviceGraphScript.setAttribute('src', '//assets.bounceexchange.com/assets/smart-tag/versioned/cjs_min_92abedfd1b9757a428bfcd7452d0081f.js');
			deviceGraphScript.setAttribute('async', 'async');
			var dgAttrs = [{"Key":"id","Value":"c.js"},{"Key":"async","Value":"true"},{"Key":"data-apikey","Value":"2^HIykD"},{"Key":"data-cb","Value":"bouncex.dg.initPostDeviceGraph"},{"Key":"data-bx","Value":"1"},{"Key":"data-gm","Value":"1"},{"Key":"data-fire","Value":"1"},{"Key":"data-adcb","Value":"bouncex.dg.getAdsOptStatus"}];
			if (dgAttrs) {
				for (var i = 0; i < dgAttrs.length; i++) {
					deviceGraphScript.setAttribute(dgAttrs[i].Key, dgAttrs[i].Value);
				}
			}
			document.body.appendChild(deviceGraphScript);

			bouncex.initializeTag = function() {};
		};

		runtime.onload = bouncex.initializeTag;
		document.body.appendChild(runtime);

	}


}

if (document.readyState === "loading") {
	document.addEventListener("DOMContentLoaded", bxBootstrap);
} else {
	bxBootstrap();
}})();