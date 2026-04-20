(function(){
  const api = document.currentScript['data-api'];
  const pname = document.currentScript['data-pname'];
  const voxMacros = {};
  try{

    if (window.origin.includes('amp') || window.origin.includes('safeframe')){

      //USED FOR AMP PLAYERS//
      setAmpMacros(voxMacros, pname)

    }else{

      //USED FOR WEB PLAYERS//
      setConcertAds(voxMacros);
      setDV(api, voxMacros);
      setPermutive(voxMacros);
      setAdContext(voxMacros);

      voxMacros.cust_params = createCustParams(voxMacros, pname);
    }

  }catch(e){
    console.log(e);
  }

  api.setMacros(voxMacros);

}());

function setConcertAds(voxMacros){
  voxMacros.entry_type = "",
    voxMacros.entry_id = "",
    voxMacros.entry_group = "",
    voxMacros.affiliation = "",
    voxMacros.cts_keyword_list = "", 
    voxMacros.cts_keyword = "",
    voxMacros.cts_keyword_age = "",
    voxMacros.cts_iab_category = "",
    voxMacros.cts_present = "",
    voxMacros.kw = "",
    voxMacros.pn = "",
    voxMacros.network = "",
    voxMacros.page_type = "",
    voxMacros.team = "";


  if (top.window.CONCERT_ADS_CONFIG &&
      top.window.CONCERT_ADS_CONFIG.dfpVariables){
    voxMacros.entry_type = top.window.CONCERT_ADS_CONFIG.dfpVariables.entry_type, 
      voxMacros.entry_group = top.window.CONCERT_ADS_CONFIG.dfpVariables.entry_group,
      voxMacros.affiliation = top.window.CONCERT_ADS_CONFIG.dfpVariables.affiliation,
      voxMacros.entry_id = top.window.CONCERT_ADS_CONFIG.dfpVariables.entry_id;
  }

  if (top.window.concertAds && 
      top.window.concertAds.variables){
    voxMacros.cts_keyword_list = top.window.concertAds.variables.cts_keyword_list, 
      voxMacros.cts_keyword = top.window.concertAds.variables.cts_keyword, 
      voxMacros.cts_keyword_age = top.window.concertAds.variables.cts_keyword_age,
      voxMacros.cts_iab_category = top.window.concertAds.variables.cts_iab_category,
      voxMacros.team = top.window.concertAds.variables.team,
      voxMacros.cts_present = top.window.concertAds.variables.cts_present,
      voxMacros.kw = top.window.concertAds.variables.kw,
      voxMacros.pn = top.window.concertAds.variables.pn,
      voxMacros.network = top.window.concertAds.variables.network,
      voxMacros.page_type = top.window.concertAds.variables.page_type;
  }

}

function setDV(api, voxMacros){
  voxMacros.IDS = "",
    voxMacros.ABS = "",
    voxMacros.BSC = "";


  if(top.window.PQ &&
     top.window.PQ.PTS){
    voxMacros.IDS = top.window.PQ.PTS.IDS.toString(), 
      voxMacros.ABS = top.window.PQ.PTS.ABS.toString(),
      voxMacros.BSC = top.window.PQ.PTS.BSC.toString();

  } else if(top.window.PQ) {
    top.window.PQ = top.window.PQ || { cmd: [] };
    top.window.PQ.cmd.push(async function () {
      try{
        top.window.PQ.getTargeting({
          signals: ["bsc", 'abs', 'ids']
        }, function (err, data) {
          if (err)console.log('Unable to get DoubleVerify targeting');
          else {
            voxMacros.IDS = top.window.PQ.PTS.IDS.toString(), 
              voxMacros.ABS = top.window.PQ.PTS.ABS.toString(),
              voxMacros.BSC = top.window.PQ.PTS.BSC.toString();

            api.setMacros({
              BSC: data.BSC ? data.BSC.toString() : "", 
              ABS: data.ABS ? data.ABS.toString() : "",
              IDS: data.IDS ? data.IDS.toString() : "",
              cust_params: createCustParams(voxMacros),
            });
          }
        })
      }catch(e){console.log('Unable to get DoubleVerify targeting')}
    });

  }

}

function setPermutive(voxMacros){
  voxMacros.permutive = "";
  if (window.localStorage.getItem("_pdfps")){
    voxMacros.permutive = JSON.parse(top.window.localStorage.getItem("_pdfps")).toString();
  }

}

function setAdContext(voxMacros){
  voxMacros.channel = "",
    voxMacros.nid = "",
    voxMacros.page_type = "",
    voxMacros.tag = "";

  if (top.window.ad_context &&
      top.window.ad_context.page_targeting){
    voxMacros.channel = top.window.ad_context.page_targeting.channel, 
      voxMacros.nid = top.window.ad_context.page_targeting.nid,
      voxMacros.page_type = top.window.ad_context.page_targeting.page_type,
      voxMacros.tag = top.window.ad_context.page_targeting.tag;
  }




}

function createCustParams(voxMacros, pname){
  let cust_params_string = `player_name=${pname}`;
  console.log(cust_params_string);

  for (let key in voxMacros){
    if (!voxMacros[key]){
      delete voxMacros[key];
    } else {
      cust_params_string += `&${key}=${voxMacros[key]}`;
    }
  }

  //cust_params_string = cust_params_string.substring(1);
  return cust_params_string;

}

function setAmpMacros(voxMacros, pname){
  const ampVoxMacros = window.cnxVoxMacro || window.cnxVoxMacros;

  if (ampVoxMacros){
    voxMacros.cust_params = `player_name=${pname}`;
    for (let key in ampVoxMacros){ 
      voxMacros[key] = ampVoxMacros[key];
      voxMacros.cust_params += `&${key}=${ampVoxMacros[key]}`;
    }
    //voxMacros.cust_params = voxMacros.cust_params.substring(1);
    //return cust_params_string;
  }

}

