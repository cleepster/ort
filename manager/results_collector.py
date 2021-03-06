import os 
import sys
import json
from subprocess import Popen,PIPE
from include import Json
from include import Sqlite
from include import SendMessage
from collections import OrderedDict
from include import Psql
from include import CreateAnimEntry


class ResultsCollector():
    def __init__(self, host, meta_file, sim_id):# {{{
        '''
        1. aamksrun makes gearman pass these jobs to workers:
            /usr/local/aamks/tests/worker.py
        2. Worker calls gearman server aOut function
        3. This file implements gearman's aOut function:
            * download results.json with configuration to workers/123/report_123.json
            * download animation.zip to workers/123/anim.zip
        '''
        self.host = host
        self.meta_file = meta_file
        self.sim_id = int(sim_id)
        self.meta = None
        self.json = Json()
        SendMessage(host + meta_file + sim_id)

        if os.environ['AAMKS_WORKER'] == 'gearman':
            self._fetch_meta()
            self.meta = self.json.read(self.meta_file)
            self._get_meta_animation()
            self.s = Sqlite("{}/aamks.sqlite".format(self.meta['path_to_project']))
            self._animation_save()
            self.psql_report()
        else:
            self.meta = self.json.read(self.meta_file)
            self.s = Sqlite("{}/aamks.sqlite".format(self.meta['path_to_project']))
            self._animation_save()
            self.psql_report()
#}}}

    def _fetch_meta(self):# {{{
        try:
            Popen(["scp", "{}:{}".format(self.host, self.meta_file), self.meta_file]).wait()
            SendMessage("self.meta copied")
        except Exception as e:
            SendMessage(e)
        else:
            pass
#}}}
    def _get_meta_animation(self):
        source = self.host+':'+self.meta['path_to_project']+'workers/'+str(self.meta['sim_id'])+'/'+self.meta['animation']
        dest = self.meta['path_to_project']+'workers/'+str(self.meta['sim_id'])+'/'+self.meta['animation']
        SendMessage(source + " " + dest)
        Popen(["scp", source, dest])
        SendMessage("Animation data copied")
#}}}

    def _animation_save(self):# {{{
        params=OrderedDict()
        params['sort_id']=self.sim_id
        params['title']="sim.{}".format(self.sim_id)
        params['srv']=0
        params['fire_origin'] = self.s.query("select floor, x, y from fire_origin where sim_id=?", (self.sim_id,))[0]
        params['highlight_geom']=None
        params['anim']="{}/{}_{}_{}_anim.zip".format(self.sim_id, self.meta['project_id'], self.meta['scenario_id'], self.sim_id)

        cae=CreateAnimEntry()
        cae.save(params, "{}workers/anims.json".format(self.meta['path_to_project']))
        SendMessage("Animation updated and saved")
#}}}
    def psql_report(self):
        p = Psql()
        fed=json.dumps(self.meta['psql']['fed'])
        rset = json.dumps(self.meta['psql']['rset'])
        i_risk = json.dumps(self.meta['psql']['i_risk'])
        query = "SELECT Count(*) FROM fed_growth_cells_data where project_id = {} AND scenario_id = {} ".format(self.meta['project_id'], self.meta['scenario_id'])
        results = p.query(query)
        count = [i[0] for i in results]
        if count[0] == 0:
            for key in self.meta['psql']['fed_heatmaps_table_schema']:
                for i in range(len(self.meta['psql']['fed_heatmaps_table_schema'][key])):
                    for j in range(len(self.meta['psql']['fed_heatmaps_table_schema'][key][0])):
                        values = (self.meta['psql']['fed_heatmaps_table_schema'][key][i][j]["number"],self.meta['scenario_id'],self.meta['project_id'],self.meta['psql']['fed_heatmaps_table_schema'][key][i][j]["floor"],self.meta['psql']['fed_heatmaps_table_schema'][key][i][j]["x_min"],self.meta['psql']['fed_heatmaps_table_schema'][key][i][j]["x_max"],self.meta['psql']['fed_heatmaps_table_schema'][key][i][j]["y_min"],self.meta['psql']['fed_heatmaps_table_schema'][key][i][j]["y_max"],0,0)
                        p.query("INSERT INTO fed_growth_cells_data(cell_id, scenario_id, project_id, floor, x_min, x_max, y_min, y_max, fed_growth_sum, samples_number) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", values)
        
        for key in self.meta['psql']['fed_heatmaps_data_to_insert']:
            for row in self.meta['psql']['fed_heatmaps_data_to_insert'][key]:
                query = "UPDATE fed_growth_cells_data SET fed_growth_sum = fed_growth_sum + {}, samples_number = samples_number + {} WHERE cell_id={} and scenario_id={} and project_id={} and floor={}".format(round(row["sum"],2), row["count"], row['cell_number'], self.meta['scenario_id'], self.meta['project_id'], int(key))
                p.query(query)

        p.query("UPDATE simulations SET fed = '{}', wcbe='{}', run_time = {}, dcbe_time = {}, min_vis_compa = {}, max_temp = {}, host = '{}', min_hgt_compa = {}, min_vis_cor = {}, min_hgt_cor = {} WHERE project=%s AND scenario_id=%s AND iteration=%s".format(fed, rset, self.meta['psql']['runtime'], self.meta['psql']['cross_building_results']['dcbe'], self.meta['psql']['cross_building_results']['min_vis_compa'], self.meta['psql']['cross_building_results']['max_temp_compa'], self.meta['worker'], self.meta['psql']['cross_building_results']['min_hgt_compa'],self.meta['psql']['cross_building_results']['min_vis_cor'],self.meta['psql']['cross_building_results']['min_hgt_cor']), (self.meta['project_id'], self.meta['scenario_id'], self.meta['sim_id']))
        p.query("UPDATE simulations SET i_risk = '{}' WHERE project=%s AND scenario_id=%s AND iteration=%s".format(i_risk), (self.meta['project_id'], self.meta['scenario_id'], self.meta['sim_id']))
        SendMessage("Database updated")

try:
    host = sys.argv[1]
    meta_file = sys.argv[2]
    sim_id = sys.argv[3]
    ResultsCollector(host, meta_file, sim_id)
except Exception as e:
    SendMessage(e)


