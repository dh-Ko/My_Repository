using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Windows.Input;

namespace WinApp1
{
    public partial class frmInput : Form
    {
        public frmInput(string str = "", int x = 0, int y = 0)  // 초기값 설정
        {
            InitializeComponent();
            label1.Text = str;
            Location = new Point(x, y);
        }
        public string sRet = "";
        private void textBox1_KeyPress(object sender, KeyPressEventArgs e)
        {
            if (e.KeyChar == '\r') // [Enter]키 pressed / (13:0d)
            {
                sRet = textBox1.Text;
                DialogResult = DialogResult.OK;
                Close();
            }

            else if (e.KeyChar == (char)Keys.Escape)
            {
                DialogResult = DialogResult.Cancel;
                Close();
            }
        }
    }
}
