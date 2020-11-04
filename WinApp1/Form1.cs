using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Data.SqlClient;
using System.Drawing;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace WinApp1
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }
        string sConString = @"Data Source=(LocalDB)\MSSQLLocalDB;AttachDbFilename=D:\C#\MyTable.mdf;Integrated Security=True;Connect Timeout=30";
        SqlConnection sConn = new SqlConnection();        // Database File에 연결 : ms-sql
        SqlCommand sCmd = new SqlCommand();          // SQL 명령문 처리
        

        private void mnuAddColumn_Click(object sender, EventArgs e)
        {
            frmInput dlg = new frmInput();
            dlg.ShowDialog();
            string str = dlg.sRet;
            if (str != "")
            {
                dataGridView1.Columns.Add(str, str);
            }
        }

        private void mnuAddRow_Click(object sender, EventArgs e)
        {
            dataGridView1.Rows.Add();
        }

        public string GetToken(int index, string str, string sdel)
        {   // str 문자열을 'sDel' 구분자로 분할하여 그 중 index 번째의 문자열을 반환
            // ex)  GetToken(3, "0|1|2|3|4|5", "|") ==> "3" 반환
            string[] sArr = str.Split(sdel[0]);
            return sArr[index];
        }
        private void mnuDBOpen_Click(object sender, EventArgs e)
        {
            int i;
            try
            {
                openFileDialog1.ValidateNames = false;
                if(openFileDialog1.ShowDialog() == DialogResult.OK)
                {   // Database 연결문자열을 구성.
                    // openFileDialog1.FileName : 선택된 파일의 전체 경로
                    string[] sArr = sConString.Split(';'); // 4개의 Field 중 2번째 Field(AttachDbFilename) 수정 필요
                    // string sConnStr = string.Format("{0};AttachDbFilename={1};{2};{3}", sArr[0], openFileDialog1.FileName, sArr[2], sArr[3]);
                    string sConnStr1 = $"{sArr[0]};AttachDbFilename={openFileDialog1.FileName};{sArr[1]};{sArr[2]};{sArr[3]}";
                    sConn.ConnectionString = sConnStr1;
                    sConn.Open();
                    sCmd.Connection = sConn;

                    StatusLabel1.Text = openFileDialog1.SafeFileName;
                    StatusLabel1.BackColor = Color.Green;

                    DataTable dt = sConn.GetSchema("Tables");
                    for(i = 0; i < dt.Rows.Count; i++)
                    {
                        string str = dt.Rows[i].ItemArray[2].ToString(); // 2번째 배열요소가 Table 이름
                        tbSql.Text += str + "\r\n";
                        stCombo1.DropDownItems.Add(str);    //stComboBox1.Items.Add(str);
                        stCombo1.Text = str;
                    }
                }
            }
            catch(Exception e1)
            {   // Database File Open Error 발생
                MessageBox.Show(e1.Message);
                StatusLabel1.Text = "Database Open Failed!!";
                StatusLabel1.BackColor = Color.Red;
            }
        }

        private void mnuDBClose_Click(object sender, EventArgs e)
        {
            sConn.Close();
            StatusLabel1.Text = "Database Closed";
            StatusLabel1.BackColor = Color.Gray;
        }

        private void mnuTestCmd1_Click(object sender, EventArgs e)
        {
            string sTime = $"{DateTime.Now:s}";
            string str = $"insert into fStatus values('10001','10.50','50.00','02.00','{sTime}')"; // SQL Insert 문
            RunSql(str);
        }                               

        private void mnuTestCmd2_Click(object sender, EventArgs e)
        {
            string sTime = $"{DateTime.Now:s}";
            string str = $"insert into fStatus (fCode, Temp, Hum, Wind) values ('10002','10.50','50.00','02.00')"; // SQL Insert 문
            RunSql(str);
        }
        // 함수 일반화 #n
        // 함수명 : void RunSql(string Sql)
        // 인수 : string Sql : 조회값이 없는 SQL 명령어 (Insert, Update, Delete)
        //                     Select 문을 포함한 Sql 문.
        // 리턴값 : void        select * from [table_name] SELECT Select
        public void RunSql(string Sql)
        {
            try
            {   // 첫 번째 단어 분리하고 소문자로 변환
                string s1 = GetToken(0, Sql, " ").ToLower();    // ToLower로 Sql 값을 모두 소문자로 변환 복사
                sCmd.CommandText = Sql;                
                if(s1 != "select")
                {
                    sCmd.ExecuteNonQuery();     // 조회값이 없는 SQL 명령어 수행
                    StatusLabel2.Text = "Success!";
                    StatusLabel2.BackColor = Color.Blue;
                }
                else                           // 조회된 Select 결과를 GridView에 기록
                {              // select * from [Table_Name]                 
                    int i, j;
                    dataGridView1.Rows.Clear();
                    dataGridView1.Columns.Clear();
                    string s2 = GetToken(1, Sql, " ");  // Column 명이 '*'인지를 판단
                    if(s2 == "*")
                    {
                        stCombo1.Text = GetToken(3, Sql, " ");
                    }
                    else
                    {
                        stCombo1.Text = "";
                    }

                    SqlDataReader sr = sCmd.ExecuteReader();    // Record 단위로 처리

                    for(i = 0; i < sr.FieldCount; i++)
                    {
                        dataGridView1.Columns.Add(sr.GetName(i), sr.GetName(i));
                    }
                    for (i = 0; sr.Read(); i++)    //sr.Read() : 읽을 데이터가 있으면 True, 없으면 False
                    {
                        dataGridView1.Rows.Add();
                        for(j = 0; j < sr.FieldCount; j++)
                        {
                            dataGridView1.Rows[i].Cells[j].Value = sr.GetValue(j).ToString().Trim();
                        }  
                    }
                    sr.Close();
                }                        
                StatusLabel2.Text = "Success!";
                StatusLabel2.BackColor = Color.Blue;
            }
            catch(Exception e1)
            {
                StatusLabel2.Text = e1.Message;
                StatusLabel2.BackColor = Color.Red;
            }
        }

        private void mnuTestCmd3_Click(object sender, EventArgs e)
        {
            RunSql("Select * from facility");
            stCombo1.Text = "facility";
        }

        private void dataGridView1_CellBeginEdit(object sender, DataGridViewCellCancelEventArgs e)
        {
            int x = e.ColumnIndex;
            int y = e.RowIndex;
            dataGridView1.Rows[y].Cells[x].ToolTipText = ".";
            string sHeader = dataGridView1.Columns[x].HeaderText;   // Field 명
        }

        private void mnuDBUpdate_Click(object sender, EventArgs e)
        {   //update [table_name] set [Field_name] = '[Cell_Value]' where [ID] = [ID_VALUE]
            int i, j;
            for(i=0; i < dataGridView1.RowCount; i++)   // Row indexing
            {
                for(j=0; j<dataGridView1.ColumnCount; j++)  // Column indexing
                {
                    if(dataGridView1.Rows[i].Cells[j].ToolTipText == ".")
                    {
                        string tn = stCombo1.Text;      // Table_Name
                        string fn = dataGridView1.Columns[j].HeaderText;    // Field_Name
                        string cv = dataGridView1.Rows[i].Cells[j].Value.ToString();    // Cell_Value
                        string iv = dataGridView1.Columns[0].HeaderText;    // id_Field
                        string jv = dataGridView1.Rows[i].Cells[0].Value.ToString();    // id_Value
                        string Sql = $"update {tn} set {fn} = N'{cv}' where {iv} = '{jv}'";
                        RunSql(Sql);
                        dataGridView1.Rows[i].Cells[j].ToolTipText = "";
                    }
                }
            }
        }

        private void stCombo1_DropDownItemClicked(object sender, ToolStripItemClickedEventArgs e)
        {
            string str = e.ClickedItem.Text;    // Table 명
            stCombo1.Text = str;
            RunSql($"Select * from {str}");
        }

        private void tbSql_KeyPress(object sender, KeyPressEventArgs e)
        {
            if (e.KeyChar == '\r')
            {
                string str = tbSql.Text.Trim();
                // 마지막 문장 (Enter Key입력 기준) 추출 
                // [ENTER] key value : '\r' CR(Carrage Return) + 
                // 실제 Text에는 '\r\n' ('\n'이 추가됨.)
                // Solution : '\r' 값을 구분자로 하는 GetToken 기법 사용
                string[] bStr = str.Split('\r');
                string Result = bStr.Last().Trim(); // Trim : White Space 제거
                string s1 = GetToken(0, Result, " ").ToLower();
                if(s1 == "select" || s1 == "insert" || s1 == "update" || s1 == "delete" || s1 == "create" || s1 == "alter")
                {
                    RunSql(Result);
                }
            }
        }

        private void mnuExcuteSql_Click(object sender, EventArgs e)
        {
            string str = tbSql.SelectedText;    // tbSql(텍스트박스) 내에서 선택된 텍스트를
            RunSql(str);                        // 실행한다.
        }

        private void mnuSaveTable_Click(object sender, EventArgs e)
        {
            int i, j;
            string sTable = stCombo1.Text;
            if(sTable == "")    // Table 명이 없으므로 새로운 Table 생성
            {   // create table [Table_Name] ([Col_Name] nchar(20), 
                frmInput dlg = new frmInput();
                dlg.ShowDialog();
                sTable = dlg.sRet;
                string sql = $"create table {sTable} (";
                for(i=0; i<dataGridView1.ColumnCount; i++)
                {
                    string s1 = dataGridView1.Columns[i].HeaderText;
                    string sCol = $"{s1} nchar(20)";
                    if (i < dataGridView1.ColumnCount - 1) sCol += ",";
                    sql += sCol;
                }
                sql += ")";
                RunSql(sql);
                for(i=0; i<dataGridView1.RowCount; i++)
                {
                    sql = $"insert into {sTable} values (";
                    for(j=0; j<dataGridView1.ColumnCount; j++)
                    {
                        sql += $"'{dataGridView1.Rows[i].Cells[j].Value}'";
                        if (j < dataGridView1.ColumnCount - 1) sql += ",";
                    }
                    sql += ")";
                    RunSql(sql);
                }
            }
            else   // 기존 Table이 있는 경우 Update
            {
                for(i=0; i<dataGridView1.RowCount-1; i++)
                {
                    for (j = 0; j < dataGridView1.ColumnCount; j++)
                    { 
                        dataGridView1.Rows[i].Cells[j].ToolTipText = ",";
                    }
                }
                mnuDBUpdate_Click(sender, e);
            }
        }
    }
}
